import json
import logging
import re

from shared.sdk_wrapper import Agent

from models.synthesis import ResearchSynthesis

from main_workflow.state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """Agent for synthesizing research findings."""

    def __init__(self):
        self.logger = logging.getLogger("agent.synthesis")

    async def execute(
        self, state: WorkflowState, db: MongoDBClient
    ) -> ResearchSynthesis:
        """Synthesize all research findings into coherent report."""
        self.logger.info("Synthesizing research findings")

        # Retrieve all data
        sources = await db.find_documents("research_sources", {"run_id": state.run_id})
        graph_nodes = await db.find_documents(
            "knowledge_graph", {"run_id": state.run_id}
        )

        # Create comprehensive data summary
        all_facts = []
        all_topics = set()

        for source in sources:
            for fact in source.get("key_facts", []):
                all_facts.append(
                    {
                        "fact": fact.get("fact", ""),
                        "source": source.get("title", ""),
                        "confidence": fact.get("confidence", 0.5),
                    }
                )
            all_topics.update(source.get("topics", []))

        # Use SDK Agent for synthesis (no MCP tools needed)
        async with Agent(
            name="research_synthesizer",
            description="Research synthesis specialist",
            system_prompt="""You are a research synthesis expert.

Analyze the provided research context and create a comprehensive report with TWO TEXT FORMATS:

1. TEXT REPORT: Formatted for visual reading
   - Use clear section headers (# Main Findings, ## Details)
   - Use numbered lists for findings (1., 2., 3.)
   - Use bullet points for details (-, *)
   - Professional document style with structure

2. AUDIO SCRIPT: Natural narrative for text-to-speech
   - Conversational, podcast-style narration
   - NO bullet points, numbers, or visual formatting
   - Smooth transitions: "First finding shows..." instead of "1. Finding..."
   - Natural speech flow: "Interestingly," "However," "Finally,"
   - Address listener: "Welcome to this research report..."
   - MUST BE MAXIMUM 5000 CHARACTERS (strict limit for TTS)

Return JSON with:
{
  "main_findings": ["finding 1", "finding 2", ...],
  "conflicting_viewpoints": [
    {"viewpoint_a": "...", "viewpoint_b": "...", "sources": ["...", "..."]}
  ],
  "knowledge_gaps": ["gap 1", "gap 2", ...],
  "confidence_levels": {"finding_1": 0.9, "finding_2": 0.7},
  "text_report": "# Research Synthesis\n\n## Main Findings\n\n1. First finding...\n\n2. Second finding...",
  "audio_script": "Welcome to this research synthesis. After analyzing the sources, we discovered three key findings. First, our research reveals that..."
}""",
        ) as agent:
            research_context = {
                "original_query": state.query,
                "total_sources": len(sources),
                "topics_covered": list(all_topics),
                "key_facts": all_facts[:20],  # Top 20 facts
                "knowledge_graph_size": len(graph_nodes),
            }

            response_text = await agent.query(
                f"Research context:\n{json.dumps(research_context, indent=2)}\n\nGenerate synthesis."
            )

        # Log the raw response for debugging
        self.logger.debug(f"Agent response (first 500 chars): {response_text[:500]}")

        # Parse response - try multiple patterns
        json_str = None

        # Try code block format first
        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            self.logger.debug("Found JSON in code block")

        # Try plain JSON object
        if not json_str:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                self.logger.debug(f"Extracted JSON from text, length: {len(json_str)}")

        # Last resort - empty object
        if not json_str:
            self.logger.warning("No JSON found in response, using empty object")
            json_str = "{}"

        try:
            synthesis_data = json.loads(json_str)
            self.logger.info(f"Successfully parsed JSON with {len(synthesis_data)} keys")

            # Enforce 5000 character limit on audio_script
            audio_script = synthesis_data.get("audio_script", "")
            if len(audio_script) > 5000:
                self.logger.warning(
                    f"Audio script exceeded 5000 characters ({len(audio_script)}). Truncating..."
                )
                # Truncate at word boundary near 5000 chars
                audio_script = audio_script[:4990]
                last_space = audio_script.rfind(" ")
                if last_space > 4500:  # Ensure we don't cut too much
                    audio_script = audio_script[:last_space] + "..."
                else:
                    audio_script = audio_script[:4997] + "..."

            synthesis = ResearchSynthesis(
                run_id=state.run_id,
                main_findings=synthesis_data.get("main_findings", []),
                conflicting_viewpoints=synthesis_data.get("conflicting_viewpoints", []),
                knowledge_gaps=synthesis_data.get("knowledge_gaps", []),
                confidence_levels=synthesis_data.get("confidence_levels", {}),
                sources_used=[str(s.get("_id", "")) for s in sources],
                text_report=synthesis_data.get("text_report", ""),
                audio_script=audio_script,
            )
        except Exception as e:
            self.logger.error(f"Failed to parse synthesis response: {e}")
            self.logger.error(f"JSON string attempted: {json_str[:1000]}")
            self.logger.error(f"Full response text: {response_text[:2000]}")
            synthesis = ResearchSynthesis(
                run_id=state.run_id,
                main_findings=["Synthesis unavailable"],
                conflicting_viewpoints=[],
                knowledge_gaps=[],
                confidence_levels={},
                sources_used=[],
                text_report="Synthesis unavailable",
                audio_script="Synthesis is currently unavailable for this research.",
            )

        # Store synthesis in MongoDB
        synthesis_dict = synthesis.model_dump()
        synthesis_id = await db.insert_document("research_syntheses", synthesis_dict)

        self.logger.info(
            f"Research synthesis complete: {len(synthesis.main_findings)} findings"
        )
        return synthesis
