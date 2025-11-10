import json
import logging
import re
from datetime import datetime
from typing import Any, Dict

from shared.sdk_wrapper import Agent

from models.synthesis import ResearchSynthesis

from main_workflow.state import WorkflowState

logger = logging.getLogger(__name__)


class AudioReportAgent:
    """Agent for generating audio reports using ElevenLabs text-to-speech."""

    def __init__(self):
        self.logger = logging.getLogger("agent.audio_report")

    async def execute(
        self,
        state: WorkflowState,
        test_mode: bool = True,  # Set to False when ready for production
    ) -> Dict[str, Any]:
        """
        Generate audio report from research synthesis using ElevenLabs and store in MinIO.

        Args:
            state: Workflow state with synthesis data
            test_mode: If True, skip ElevenLabs audio generation but generate full report text (default: True)

        Returns:
            Dictionary with audio_id, minio_urls, and metadata
        """
        self.logger.info("Starting audio report generation")

        # Validate synthesis exists
        if not state.synthesis:
            raise ValueError("State synthesis is None. Cannot generate audio report.")

        # Convert synthesis dict to ResearchSynthesis object
        synthesis = (
            ResearchSynthesis(**state.synthesis)
            if isinstance(state.synthesis, dict)
            else state.synthesis
        )

        # Extract pre-generated text reports from synthesis
        text_report = synthesis.text_report  # For visual reading (MinIO text file)
        audio_script = synthesis.audio_script  # For TTS narration

        self.logger.info(
            f"Using pre-generated text report: {len(text_report)} characters"
        )
        self.logger.info(
            f"Using pre-generated audio script: {len(audio_script)} characters"
        )

        if test_mode:
            self.logger.warning(
                "🧪 TEST MODE: Skipping ElevenLabs audio generation to save API credits"
            )
        else:
            self.logger.info("📝 PRODUCTION MODE: Generating audio with ElevenLabs")

        # Generate unique audio ID
        audio_id = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # File names for MinIO
        text_filename = f"research_reports/{state.run_id}/{audio_id}_report.txt"
        audio_filename = f"research_reports/{state.run_id}/{audio_id}_audio.mp3"

        voice_name = "ChO6kqkVouUn0s7HMunx (Pete - Natural Conversations)"
        output_dir = "/home/lukas/Temp/elevenlabs-files"

        # Initialize result variable
        result = None

        if test_mode:
            # Test mode: Skip ElevenLabs, create mock result
            self.logger.info(
                "Test mode: Creating mock audio result without calling ElevenLabs"
            )
            result = {
                "success": True,
                "audio_file_path": None,  # No actual file in test mode
                "duration_seconds": len(audio_script) // 15,  # Estimate: 15 chars/sec
                "voice_used": voice_name,
                "character_count": len(audio_script),
                "test_mode": True,
            }
        else:
            # Production mode: Use SDK Agent with ElevenLabs MCP server
            async with Agent(
                name="audio_generator",
                description="Audio generation specialist using ElevenLabs TTS",
                system_prompt="""You are an audio generation agent with access to ElevenLabs TTS via MCP.

Your only job:
1. Generate audio from text using ElevenLabs text-to-speech
2. Return the file path where ElevenLabs saved the audio
3. Return metadata about the audio (duration, voice used, character count)""",
                mcp_servers=["elevenlabs"],
            ) as agent:

                prompt = f"""Generate audio from text using ElevenLabs. Execute EXACTLY once:

AUDIO SCRIPT TO CONVERT (optimized for natural speech):
{audio_script}

INSTRUCTIONS:
1. Use mcp__elevenlabs__text_to_speech tool ONCE with these parameters:
   - text: The audio script above (optimized for TTS)
   - voice: {voice_name}
   - output_directory: {output_dir}
2. Note the EXACT FULL FILE PATH where ElevenLabs saved the audio file

CRITICAL:
- Generate audio ONLY ONCE. Do NOT regenerate.
- Return the EXACT file path from the ElevenLabs tool response
- The path must be an absolute path to the generated MP3 file

RETURN JSON (copy the exact file path from the tool response):
{{
  "success": true,
  "audio_file_path": "<EXACT full absolute path from ElevenLabs tool>",
  "duration_seconds": <actual_duration>,
  "voice_used": "<voice_id_used>",
  "character_count": {len(audio_script)}
}}

If generation fails:
{{
  "success": false,
  "error": "<error message>"
}}"""

                response = await agent.query(prompt)

                self.logger.info(f"Agent response: {response[:500]}...")

                # Parse response - look for JSON
                try:
                    # Try to extract JSON from response
                    json_match = re.search(r"\{[^}]+\}", response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        self.logger.info(f"Parsed result: {result}")

                        # Validate that we got a file path
                        if result.get("success") and not result.get("audio_file_path"):
                            # Try to extract file path from the response text
                            path_match = re.search(
                                r"(/[^\s\"']+\.mp3|[A-Z]:[^\s\"']+\.mp3)", response
                            )
                            if path_match:
                                result["audio_file_path"] = path_match.group(1)
                                self.logger.info(
                                    f"Extracted file path from response: {result['audio_file_path']}"
                                )
                            else:
                                result["success"] = False
                                result["error"] = "No audio file path in response"

                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"JSON parsing failed: {e}, attempting to extract path from text"
                    )
                    # Try to extract file path directly from response
                    path_match = re.search(
                        r"(/[^\s\"']+\.mp3|[A-Z]:[^\s\"']+\.mp3|~/[^\s\"']+\.mp3)",
                        response,
                    )
                    if path_match:
                        result = {
                            "success": True,
                            "audio_file_path": path_match.group(1),
                            "duration_seconds": len(audio_script)
                            // 15,  # Rough estimate: 15 chars/sec
                            "voice_used": voice_name,
                            "character_count": len(audio_script),
                        }
                        self.logger.info(
                            f"Extracted file path: {result['audio_file_path']}"
                        )

                if not result:
                    # If no JSON found, assume failure
                    self.logger.error("Could not parse response or extract file path")
                    result = {
                        "success": False,
                        "error": "Agent did not return valid JSON or file path",
                        "duration_seconds": 0,
                        "voice": voice_name,
                        "character_count": len(audio_script),
                    }

                # Expand ~ to home directory if needed
                if result.get("audio_file_path") and result[
                    "audio_file_path"
                ].startswith("~/"):
                    import os

                    result["audio_file_path"] = os.path.expanduser(
                        result["audio_file_path"]
                    )

        # Build return metadata
        audio_metadata = {
            "query": state.query,
            "run_id": state.run_id,
            "audio_id": audio_id,
            "audio_filename": result.get(
                "audio_file_path", audio_filename
            ),  # Use actual file path from ElevenLabs
            "audio_filename_minio": audio_filename,  # MinIO destination path
            "text_filename": text_filename,
            "report_text": text_report,  # Visual text report for MinIO upload
            "audio_script": audio_script,  # Audio script that was narrated
            "character_count": result.get("character_count", len(audio_script)),
            "created_at": datetime.now().isoformat(),
            "duration_seconds": result.get("duration_seconds", 0),
            "format": "mp3",
            "voice": voice_name,
            "success": result.get("success", False),
            "error": result.get("error"),
            "test_mode": test_mode,  # Include test mode flag
        }

        self.logger.info(f"Audio report complete: {audio_id}")
        if result.get("success"):
            self.logger.info(
                f"Text report uploaded to MinIO: {result.get('text_minio_url')}"
            )
            self.logger.info(
                f"Audio file uploaded to MinIO: {result.get('audio_minio_url')}"
            )
        else:
            self.logger.warning(
                f"Audio generation encountered issues: {result.get('error')}"
            )

        return audio_metadata
