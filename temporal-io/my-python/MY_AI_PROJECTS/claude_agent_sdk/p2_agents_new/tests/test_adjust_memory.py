"""
Test for adjust_memory activity.

This test can be run independently without running the full workflow.

Usage:
    uv run python -m tests.test_adjust_memory
"""

import asyncio
import logging
from datetime import datetime

from agents import AdjustMemoryAgent
from main_workflow.state import WorkflowState

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# async def test_adjust_memory_agent():
#     """Test the AdjustMemoryAgent directly."""

#     logger.info("=" * 80)
#     logger.info("Testing AdjustMemoryAgent")
#     logger.info("=" * 80)

#     # Create test state
#     test_query = "What are the latest methods for benchmarking and evaluating AI agents?"
#     test_run_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

#     state = WorkflowState(
#         query=test_query,
#         run_id=test_run_id,
#         web_sources=[],
#         academic_sources=[],
#         knowledge_graph=[],
#         synthesis=None,
#     )

#     logger.info(f"Test Query: {test_query}")
#     logger.info(f"Test Run ID: {test_run_id}")
#     logger.info("")

#     # Execute the agent
#     try:
#         agent = AdjustMemoryAgent()
#         result = await agent.execute(state=state)

#         logger.info("")
#         logger.info("=" * 80)
#         logger.info("RESULT")
#         logger.info("=" * 80)
#         logger.info(f"Success: {result.get('success')}")
#         logger.info(f"Run ID: {result.get('run_id')}")
#         logger.info(f"Query: {result.get('query')}")
#         logger.info(f"Memory Response: {result.get('memory_response')}")
#         logger.info("")

#         if result.get("success"):
#             logger.info("✅ TEST PASSED: Memory stored successfully")
#         else:
#             logger.error("❌ TEST FAILED: Memory storage failed")

#         return result

#     except Exception as e:
#         logger.error(f"❌ TEST FAILED WITH EXCEPTION: {e}")
#         raise


async def test_adjust_memory_activity():
    """Test the adjust_memory activity (includes agent + wrapper)."""

    logger.info("\n")
    logger.info("=" * 80)
    logger.info("Testing adjust_memory Activity")
    logger.info("=" * 80)

    # Import activity
    from main_workflow.activities import adjust_memory

    # Create test state
    test_query = "How can we measure whether changes to system messages improve AI agent performance?"
    test_run_id = f"test-activity-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    state = WorkflowState(
        query=test_query,
        run_id=test_run_id,
        web_sources=[],
        academic_sources=[],
        knowledge_graph=[],
        synthesis=None,
    )

    logger.info(f"Test Query: {test_query}")
    logger.info(f"Test Run ID: {test_run_id}")
    logger.info("")

    # Execute the activity directly (outside Temporal)
    try:
        result = await adjust_memory(state)

        logger.info("")
        logger.info("=" * 80)
        logger.info("RESULT")
        logger.info("=" * 80)
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Run ID: {result.get('run_id')}")
        logger.info(f"Query: {result.get('query')}")
        logger.info(f"Memory Response: {result.get('memory_response')}")
        logger.info("")

        if result.get("success"):
            logger.info("✅ TEST PASSED: Activity executed successfully")
        else:
            logger.error("❌ TEST FAILED: Activity execution failed")

        return result

    except Exception as e:
        logger.error(f"❌ TEST FAILED WITH EXCEPTION: {e}")
        raise


async def main():
    """Run all tests."""

    logger.info("\n\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "ADJUST MEMORY TESTS" + " " * 39 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")

    try:
        # # Test 1: Agent directly
        # logger.info("TEST 1: Testing AdjustMemoryAgent directly")
        # logger.info("-" * 80)
        # result1 = await test_adjust_memory_agent()

        # Test 2: Activity wrapper
        logger.info("\n\nTEST 2: Testing adjust_memory Activity")
        logger.info("-" * 80)
        result2 = await test_adjust_memory_activity()

        # Summary
        logger.info("\n\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 30 + "TEST SUMMARY" + " " * 36 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        logger.info("")
        # logger.info(f"Test 1 (Agent): {'✅ PASSED' if result1.get('success') else '❌ FAILED'}")
        logger.info(
            f"Test 2 (Activity): {'✅ PASSED' if result2.get('success') else '❌ FAILED'}"
        )
        logger.info("")

        if result2.get("success") and result2.get("success"):
            logger.info("🎉 ALL TESTS PASSED!")
            return 0
        else:
            logger.error("❌ SOME TESTS FAILED")
            return 1

    except Exception as e:
        logger.error(f"\n\n❌ TESTS FAILED WITH EXCEPTION: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
