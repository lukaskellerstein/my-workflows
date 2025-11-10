"""
Example: Simple LOOP demonstration
A minimal example showing how a workflow can loop back to previous activities.

Flow:
  Start → Activity A → Activity B → Check Condition
                ↑                         |
                |                         |
                └─────── LOOP BACK ───────┘
                       (if condition met)
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# Activity A: Prepare data
@activity.defn
def activity_a(attempt: int) -> str:
    activity.logger.info(f"🔵 [Activity A] Preparing data (attempt {attempt})")
    result = f"Data prepared on attempt {attempt}"
    activity.logger.info(f"🔵 [Activity A] Result: {result}")
    return result


# Activity B: Process data
@activity.defn
def activity_b(data: str, attempt: int) -> int:
    activity.logger.info(f"🟢 [Activity B] Processing data (attempt {attempt})")
    activity.logger.info(f"🟢 [Activity B] Input: {data}")

    # Simulate some score/result that improves with attempts
    score = attempt * 30  # Score: 30, 60, 90, ...
    activity.logger.info(f"🟢 [Activity B] Generated score: {score}")

    return score


# Activity C: Check condition
@activity.defn
def activity_c(score: int, attempt: int) -> bool:
    activity.logger.info(f"🟡 [Activity C] Checking condition (attempt {attempt})")
    activity.logger.info(f"🟡 [Activity C] Score to evaluate: {score}")

    # Condition: score must be >= 80
    threshold = 80
    passed = score >= threshold

    if passed:
        activity.logger.info(f"🟡 [Activity C] ✓ PASSED - Score {score} >= {threshold}")
    else:
        activity.logger.warning(f"🟡 [Activity C] ✗ FAILED - Score {score} < {threshold}")

    return passed


# Activity D: Finalize
@activity.defn
def activity_d(final_score: int) -> str:
    activity.logger.info(f"🔴 [Activity D] Finalizing with score: {final_score}")
    return f"Completed successfully with final score: {final_score}"


# Workflow with loop
@workflow.defn
class SimpleLoopWorkflow:
    @workflow.run
    async def run(self) -> str:
        workflow.logger.info("═══════════════════════════════════════")
        workflow.logger.info("Starting Simple Loop Workflow")
        workflow.logger.info("═══════════════════════════════════════")

        max_attempts = 5
        attempt = 0

        # THIS IS THE LOOP
        while attempt < max_attempts:
            attempt += 1
            workflow.logger.info(f"\n┌─── LOOP ITERATION {attempt} ───┐")

            # Activity A: Prepare
            workflow.logger.info("│ Executing Activity A...")
            data = await workflow.execute_activity(
                activity_a,
                attempt,
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Activity B: Process
            workflow.logger.info("│ Executing Activity B...")
            score = await workflow.execute_activity(
                activity_b,
                args=[data, attempt],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Activity C: Check condition
            workflow.logger.info("│ Executing Activity C (condition check)...")
            condition_met = await workflow.execute_activity(
                activity_c,
                args=[score, attempt],
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info("└" + "─" * 30 + "┘")

            # LOOP DECISION POINT
            if condition_met:
                workflow.logger.info(f"✓ Condition MET on attempt {attempt} - EXITING LOOP")
                # Exit loop and proceed to finalization
                break
            else:
                workflow.logger.warning(f"✗ Condition NOT MET on attempt {attempt}")

                if attempt >= max_attempts:
                    workflow.logger.error(f"Max attempts ({max_attempts}) reached!")
                    return f"Workflow failed after {max_attempts} attempts. Final score: {score}"

                # LOOP BACK: Continue to next iteration
                workflow.logger.info(f"↻ LOOPING BACK to Activity A (will be attempt {attempt + 1})")
                # The while loop continues, returning to Activity A

        # Activity D: Finalize (only reached if condition was met)
        workflow.logger.info("\n▶ Condition met! Proceeding to finalization...")
        workflow.logger.info("Executing Activity D...")
        result = await workflow.execute_activity(
            activity_d,
            score,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info("═══════════════════════════════════════")
        workflow.logger.info("Workflow Completed Successfully")
        workflow.logger.info("═══════════════════════════════════════")

        return f"{result} (total attempts: {attempt})"


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-loop-task-queue",
        workflows=[SimpleLoopWorkflow],
        activities=[activity_a, activity_b, activity_c, activity_d],
        activity_executor=ThreadPoolExecutor(5),
    ):
        print("\n" + "="*60)
        print("EXECUTING: Simple Loop Workflow")
        print("="*60)
        print("\nThis workflow will:")
        print("1. Execute Activity A (prepare)")
        print("2. Execute Activity B (process)")
        print("3. Execute Activity C (check condition)")
        print("4. IF condition NOT met → LOOP BACK to step 1")
        print("5. IF condition MET → proceed to Activity D (finalize)")
        print("\nExpected: Will loop ~3 times until score reaches 80+")
        print("="*60 + "\n")

        # Execute the workflow
        result = await client.execute_workflow(
            SimpleLoopWorkflow.run,
            id="simple-loop-workflow",
            task_queue="0-simple-loop-task-queue",
        )

        print("\n" + "="*60)
        print("FINAL RESULT:")
        print("="*60)
        print(result)
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
