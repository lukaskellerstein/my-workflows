"""
Example: LLM Call in Workflow Task

Demonstrates how to integrate LLM API calls within Prefect tasks.
Requires: pip install openai
"""

import os
from prefect import flow, task, get_run_logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

# ========== LLM Tasks ==========


@task(retries=2, retry_delay_seconds=1)
def call_llm(
    prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7
) -> dict:
    """
    Makes an LLM API call.

    Note: Requires OPENAI_API_KEY environment variable.
    """
    logger = get_run_logger()
    logger.info(f"Calling LLM with model: {model}")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )

    result = {
        "model": model,
        "prompt": prompt,
        "response": response.choices[0].message.content,
        "tokens": {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens,
        },
    }

    logger.info(f"LLM response received ({result['tokens']['total']} tokens)")
    return result


@task
def extract_data_from_text(text: str) -> dict:
    """Extracts structured data from unstructured text using LLM."""
    logger = get_run_logger()
    logger.info("Extracting structured data from text")

    prompt = f"""
Extract the following information from the text below and return as JSON:
- name: person's name
- email: email address
- phone: phone number
- company: company name

Text: {text}

Return only valid JSON, no additional text.
"""

    result = call_llm(prompt, temperature=0.0)

    # Parse JSON response
    import json

    try:
        extracted = json.loads(result["response"])
        return {"extracted_data": extracted, "tokens_used": result["tokens"]["total"]}
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON response")
        return {
            "extracted_data": None,
            "raw_response": result["response"],
            "tokens_used": result["tokens"]["total"],
        }


@task
def classify_text(text: str, categories: list[str]) -> dict:
    """Classifies text into predefined categories using LLM."""
    logger = get_run_logger()
    logger.info(f"Classifying text into {len(categories)} categories")

    prompt = f"""
Classify the following text into one of these categories: {', '.join(categories)}

Text: {text}

Respond with only the category name, nothing else.
"""

    result = call_llm(prompt, temperature=0.0)

    classification = result["response"].strip()

    return {
        "text": text,
        "classification": classification,
        "categories": categories,
        "tokens_used": result["tokens"]["total"],
    }


@task
def summarize_text(text: str, max_words: int = 50) -> dict:
    """Summarizes text using LLM."""
    logger = get_run_logger()
    logger.info(f"Summarizing text (max {max_words} words)")

    prompt = f"""
Summarize the following text in no more than {max_words} words:

{text}
"""

    result = call_llm(prompt, temperature=0.5)

    return {
        "original_length": len(text.split()),
        "summary": result["response"],
        "summary_length": len(result["response"].split()),
        "tokens_used": result["tokens"]["total"],
    }


@task
def generate_response(user_message: str, context: str = "") -> dict:
    """Generates a response to a user message."""
    logger = get_run_logger()
    logger.info("Generating response to user message")

    prompt = f"""
Context: {context}

User message: {user_message}

Generate a helpful, concise response.
"""

    result = call_llm(prompt, temperature=0.7)

    return {
        "user_message": user_message,
        "response": result["response"],
        "tokens_used": result["tokens"]["total"],
    }


# ========== Workflows ==========


@flow(name="Simple LLM Flow", log_prints=True)
def simple_llm_flow(prompt: str = "Explain Prefect workflows in one sentence."):
    """
    Simple flow that calls an LLM.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("SIMPLE LLM CALL")
    print(f"{'='*60}\n")

    print(f"Prompt: {prompt}\n")

    result = call_llm(prompt)

    print(f"Response: {result['response']}\n")
    print(f"Tokens used: {result['tokens']['total']}")

    return result


@flow(name="Text Extraction Flow", log_prints=True)
def text_extraction_flow():
    """
    Extracts structured data from unstructured text using LLM.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("TEXT EXTRACTION WITH LLM")
    print(f"{'='*60}\n")

    # Sample unstructured text
    text = """
    Hi, my name is John Smith and I work at Acme Corporation.
    You can reach me at john.smith@acme.com or call me at (555) 123-4567.
    """

    print(f"Input text: {text}\n")

    result = extract_data_from_text(text)

    print(f"Extracted data: {result['extracted_data']}\n")
    print(f"Tokens used: {result['tokens_used']}")

    return result


@flow(name="Text Classification Flow", log_prints=True)
def text_classification_flow():
    """
    Classifies multiple texts into categories using LLM.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("TEXT CLASSIFICATION WITH LLM")
    print(f"{'='*60}\n")

    categories = ["Technical", "Business", "Marketing", "Support"]

    texts = [
        "We need to refactor the database schema to improve query performance.",
        "Q3 revenue exceeded projections by 15% with strong EBITDA margins.",
        "Our new campaign targeting millennials shows 3x engagement rates.",
        "Customer is experiencing login issues with their account.",
    ]

    print(f"Categories: {', '.join(categories)}\n")

    results = []
    for text in texts:
        print(f"Text: {text[:60]}...")
        result = classify_text(text, categories)
        print(f"→ Classification: {result['classification']}\n")
        results.append(result)

    total_tokens = sum(r["tokens_used"] for r in results)
    print(f"Total tokens used: {total_tokens}")

    return results


@flow(name="Document Summarization Flow", log_prints=True)
def document_summarization_flow():
    """
    Summarizes multiple documents in parallel using LLM.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("DOCUMENT SUMMARIZATION WITH LLM")
    print(f"{'='*60}\n")

    documents = [
        """
        Artificial intelligence and machine learning have revolutionized the way we process
        and analyze data. Modern AI systems can now perform complex tasks such as natural
        language understanding, image recognition, and predictive analytics with remarkable
        accuracy. These advancements have opened up new possibilities across various industries
        including healthcare, finance, and transportation.
        """,
        """
        Climate change poses one of the greatest challenges to humanity. Rising global
        temperatures, melting ice caps, and extreme weather events are becoming more frequent.
        Scientists worldwide are calling for immediate action to reduce carbon emissions and
        transition to renewable energy sources to mitigate the worst effects of climate change.
        """,
        """
        The field of quantum computing promises to solve problems that are currently intractable
        for classical computers. By leveraging quantum mechanical phenomena such as superposition
        and entanglement, quantum computers could revolutionize fields like cryptography, drug
        discovery, and optimization problems.
        """,
    ]

    print(f"Summarizing {len(documents)} documents...\n")

    # Process documents in parallel using map
    summaries = summarize_text.map(documents, max_words=[30] * len(documents))

    # Display results
    for i, summary_result in enumerate(summaries, 1):
        print(f"Document {i}:")
        print(f"  Original: {summary_result['original_length']} words")
        print(f"  Summary: {summary_result['summary']}")
        print(f"  Summary length: {summary_result['summary_length']} words")
        print(f"  Tokens used: {summary_result['tokens_used']}\n")

    total_tokens = sum(s["tokens_used"] for s in summaries)
    print(f"Total tokens used: {total_tokens}")

    return summaries


@flow(name="Conversational Flow", log_prints=True)
def conversational_flow():
    """
    Multi-turn conversation workflow with context.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("CONVERSATIONAL FLOW WITH CONTEXT")
    print(f"{'='*60}\n")

    context = "You are a helpful assistant for a data engineering team."

    conversation = [
        "What is Prefect?",
        "How does it compare to Airflow?",
        "What are the main benefits?",
    ]

    responses = []

    for i, message in enumerate(conversation, 1):
        print(f"\nTurn {i}:")
        print(f"User: {message}")

        result = generate_response(message, context)
        print(f"Assistant: {result['response']}")

        # Update context with conversation history
        context += f"\nUser: {message}\nAssistant: {result['response']}"

        responses.append(result)

    total_tokens = sum(r["tokens_used"] for r in responses)
    print(f"\n{'='*60}")
    print(f"Conversation completed. Total tokens used: {total_tokens}")
    print(f"{'='*60}")

    return responses


# ========== Comprehensive Demo ==========


@flow(name="LLM Integration Comprehensive Demo", log_prints=True)
def comprehensive_llm_demo():
    """Runs all LLM integration examples."""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("=" * 70)
        print("⚠️  WARNING: OPENAI_API_KEY not set")
        print("=" * 70)
        print("\nTo run these examples, set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr set it in your code:")
        print("import os")
        print("os.environ['OPENAI_API_KEY'] = 'your-api-key-here'")
        print("=" * 70)
        return

    print("=" * 70)
    print("COMPREHENSIVE LLM INTEGRATION DEMONSTRATION")
    print("=" * 70)

    # Run all examples
    simple_llm_flow()
    text_extraction_flow()
    text_classification_flow()
    document_summarization_flow()
    conversational_flow()

    print("\n" + "=" * 70)
    print("All LLM integration examples completed")
    print("=" * 70)


if __name__ == "__main__":
    comprehensive_llm_demo()
