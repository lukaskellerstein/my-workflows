"""
Workflow Starter Script - Slack Human in the Loop
Start workflows via API.
"""
import asyncio
import sys


# Configuration
API_URL = "http://localhost:8005"


async def start_workflow(
    question_text: str, context: str, workflow_id: str = None
) -> str:
    """
    Start a Slack question workflow via API.

    Args:
        question_text: The question to ask
        context: Additional context
        workflow_id: Optional workflow ID

    Returns:
        The workflow ID
    """
    import aiohttp

    print(f"Question: {question_text}")
    print(f"Context: {context}")
    print("\n" + "=" * 60)

    # Call API to start workflow
    api_url = f"{API_URL}/question/start"
    payload = {
        "question": question_text,
        "context": context,
    }
    if workflow_id:
        payload["workflow_id"] = workflow_id

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                workflow_id = data["workflow_id"]
                print("✅ Workflow started successfully!")
                print(f"Workflow ID: {workflow_id}")
                print("\nThe question has been posted to Slack #human-in-loop")
                print("Waiting for someone to reply in the thread...")
            else:
                error = await response.text()
                print(f"❌ Failed to start workflow: {error}")
                return None

    print("\n" + "=" * 60)
    print("Reply in Slack thread to continue the workflow")
    print("=" * 60)

    return workflow_id


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Start with custom question: python start_workflow.py "question" "context"
        question = sys.argv[1]
        context = sys.argv[2] if len(sys.argv) > 2 else "No additional context"
        await start_workflow(question, context)
    else:
        # Default workflow
        print("=== Slack Question Workflow ===\n")
        question = "Should we proceed with the deployment?"
        context = "All tests have passed. QA team has approved. Ready for production."
        await start_workflow(question, context)


if __name__ == "__main__":
    asyncio.run(main())
