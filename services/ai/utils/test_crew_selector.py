"""
Test script for crew selector to demonstrate intelligent crew selection.
"""

from crew_selector import select_crew_for_task
from langchain_openai import ChatOpenAI


def test_crew_selection():
    """Test the crew selector with various example prompts."""

    # Test prompts covering different scenarios
    test_prompts = [
        # Financial queries
        "Show me all overdue payments for this month",
        "Which suppliers have we paid the most this year?",
        "Analyze our cost centers and budget allocation",
        "What invoices are due next week?",

        # Document queries
        "Find all contracts that expire in the next 30 days",
        "Review our employee handbook for compliance issues",
        "Summarize the latest partnership agreement",
        "Search for documents related to data privacy policy",

        # General queries
        "What employees are on vacation this week?",
        "List all pending purchase orders",
        "Who is the HR manager for the IT department?",
        "What are the company holidays this year?",
    ]

    print("=" * 80)
    print("CREW SELECTOR TEST RESULTS")
    print("=" * 80)

    # Initialize LLM (using cheaper model for testing)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 80)

        try:
            config = select_crew_for_task(prompt, llm)
            print(f"  Selected Crew: {config['crew_type']}")
            print(f"  Sub-type: {config['sub_type']}")
            print(f"  Reasoning: {config['reasoning']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_crew_selection()
