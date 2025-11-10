import logging
from typing import Dict, List

from temporalio import activity

from ..state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


@activity.defn
async def generate_audio_report(state: WorkflowState) -> Dict:
    """
    Activity 7: Generate audio report (AI Agent + ElevenLabs + MinIO + MongoDB).

    - Generate text report from synthesis
    - Convert report to speech using ElevenLabs
    - Upload text and audio to MinIO object storage
    - Store metadata in MongoDB
    """
    # Import agent only when activity executes (not in workflow sandbox)
    from agents import AudioReportAgent

    logger.info("Generating audio report with ElevenLabs and MinIO")

    # Execute audio generation agent (uses ElevenLabs only)
    agent = AudioReportAgent()
    result = await agent.execute(
        state=state,
        test_mode=True,  # TODO: Set to False when ready for production
    )

    # Deterministic upload to MinIO after agent generates audio
    if result.get("success"):
        logger.info("Audio generated successfully - uploading to MinIO")
        try:

            from minio import Minio
            from minio.error import S3Error

            minio_client = Minio(
                "localhost:9000",
                access_key="admin",
                secret_key="password123",
                secure=False,
            )

            bucket_name = "research-audio-reports"

            # Ensure bucket exists
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")

            from io import BytesIO

            # Upload text report (visual format for reading)
            text_report = result.get("report_text", "")
            text_object_name = f"{state.run_id}/report_text.txt"
            text_data = BytesIO(text_report.encode("utf-8"))
            minio_client.put_object(
                bucket_name,
                text_object_name,
                text_data,
                length=len(text_report.encode("utf-8")),
                content_type="text/plain; charset=utf-8",
            )
            logger.info(f"Uploaded text report to MinIO: {text_object_name}")

            # Upload audio script (narration format - ALWAYS upload regardless of test_mode)
            audio_script = result.get("audio_script", "")
            audio_script_object_name = f"{state.run_id}/audio_script.txt"
            audio_script_data = BytesIO(audio_script.encode("utf-8"))
            minio_client.put_object(
                bucket_name,
                audio_script_object_name,
                audio_script_data,
                length=len(audio_script.encode("utf-8")),
                content_type="text/plain; charset=utf-8",
            )
            logger.info(f"Uploaded audio script to MinIO: {audio_script_object_name}")

            # Audio file handling - skip MP3 generation in test mode
            if result.get("test_mode"):
                logger.info(
                    "Test mode: Skipping audio MP3 file upload to MinIO (script still uploaded)"
                )
                result["text_minio_url"] = f"minio://{bucket_name}/{text_object_name}"
                result["audio_script_minio_url"] = (
                    f"minio://{bucket_name}/{audio_script_object_name}"
                )
                result["audio_minio_url"] = None  # No audio MP3 in test mode
                result["success"] = True
            else:
                # Production mode: Upload audio file
                audio_file_local_path = result.get("audio_filename", "")
                # MinIO destination path
                audio_object_name = f"{state.run_id}/audio.mp3"

                # Check if file exists before uploading
                import os

                if not os.path.exists(audio_file_local_path):
                    raise FileNotFoundError(
                        f"Audio file not found at: {audio_file_local_path}. "
                        f"ElevenLabs may have saved it elsewhere."
                    )

                # Upload audio file
                minio_client.fput_object(
                    bucket_name,
                    audio_object_name,
                    audio_file_local_path,
                    content_type="audio/mpeg",
                )
                logger.info(
                    f"Uploaded audio to MinIO: {audio_object_name} from {audio_file_local_path}"
                )

                # Update result with MinIO URLs (production mode - all 3 files)
                result["text_minio_url"] = f"minio://{bucket_name}/{text_object_name}"
                result["audio_script_minio_url"] = (
                    f"minio://{bucket_name}/{audio_script_object_name}"
                )
                result["audio_minio_url"] = f"minio://{bucket_name}/{audio_object_name}"
                result["success"] = True

        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            result["error"] = f"MinIO upload failed: {str(e)}"
            result["success"] = False
        except Exception as e:
            logger.error(f"Upload to MinIO failed: {e}")
            result["error"] = f"Upload failed: {str(e)}"
            result["success"] = False
    else:
        logger.error(f"Audio generation failed: {result.get('error')}")

    # Store metadata in MongoDB
    db = MongoDBClient()
    await db.connect()
    try:
        # Make a copy for MongoDB (may contain ObjectId after insert)
        mongo_doc = dict(result)
        db_id = await db.insert_document("audio_reports", mongo_doc)
        logger.info(
            f"Audio report metadata saved to MongoDB: {result['audio_id']} (DB ID: {db_id})"
        )
    finally:
        await db.disconnect()

    logger.info(f"Audio report generated: {result['audio_id']}")
    if result.get("success"):
        logger.info(f"Text report URL: {result.get('text_minio_url')}")
        logger.info(f"Audio file URL: {result.get('audio_minio_url')}")
    else:
        logger.warning(f"Audio generation failed: {result.get('error')}")

    # Return result without MongoDB ObjectId (ensure clean dict for Temporal)
    # Convert any remaining datetime objects to ISO format strings
    clean_result = {}
    for key, value in result.items():
        if hasattr(value, "isoformat"):  # datetime object
            clean_result[key] = value.isoformat() if value else None
        else:
            clean_result[key] = value

    return clean_result
