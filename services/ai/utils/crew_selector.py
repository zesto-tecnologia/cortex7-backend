"""
Intelligent crew selector that uses LLM to determine the best crew for a task.
"""

from typing import Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class CrewSelection(BaseModel):
    """Model for crew selection decision."""

    crew_type: Literal["financial_analysis", "document_review", "general_task"] = Field(
        description="The type of crew to use for this task"
    )
    reasoning: str = Field(
        description="Brief explanation of why this crew was selected"
    )
    sub_type: str = Field(
        default="general",
        description="Sub-type for specialized crews (e.g., 'accounts_payable', 'compliance', etc.)"
    )


class CrewSelector:
    """Intelligent crew selector using LLM-based classification."""

    CREW_DESCRIPTIONS = """
    Available Crews:

    1. financial_analysis
       - Purpose: Analyze financial data, accounts payable, suppliers, and cost centers
       - Sub-types: accounts_payable, supplier_analysis, general
       - Best for: Financial queries, payment analysis, supplier reviews, budget questions, cost analysis
       - Keywords: payment, invoice, supplier, vendor, accounts payable, financial, cost, budget, expenses

    2. document_review
       - Purpose: Search, retrieve, analyze, and review company documents
       - Sub-types: compliance, summary, general
       - Best for: Document searches, contract reviews, compliance checks, document summarization
       - Keywords: document, contract, policy, file, review, compliance, legal documents, agreements

    3. general_task (fallback)
       - Purpose: Handle general business tasks with dynamic agent selection
       - Sub-types: N/A (automatically selects appropriate agents)
       - Best for: General questions, multi-domain tasks, HR queries, procurement, or anything not clearly financial or document-focused
       - Keywords: employee, vacation, HR, purchase order, general query, information lookup
    """

    def __init__(self, llm: ChatOpenAI = None):
        """
        Initialize the crew selector.

        Args:
            llm: Language model to use for classification. If None, creates a default one.
        """
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=CrewSelection)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing user requests and routing them to the appropriate specialized team.

{crew_descriptions}

Your task is to analyze the user's request and determine:
1. Which crew type is most appropriate
2. What sub-type (if applicable) should be used
3. Brief reasoning for your decision

Guidelines:
- If the request is clearly about finances, payments, or suppliers → financial_analysis
- If the request is about finding, reviewing, or analyzing documents → document_review
- If the request is general, about HR, procurement, or doesn't fit the above → general_task
- For financial_analysis sub-types:
  * accounts_payable: Questions about payments, invoices, due dates
  * supplier_analysis: Questions about vendors, supplier performance
  * general: Other financial questions
- For document_review sub-types:
  * compliance: Looking for compliance issues, risks, red flags
  * summary: Need to summarize documents
  * general: Other document queries

{format_instructions}"""),
            ("user", "{user_request}")
        ])

    def select_crew(self, user_request: str) -> CrewSelection:
        """
        Analyze the user request and select the appropriate crew.

        Args:
            user_request: The user's input message/query

        Returns:
            CrewSelection with crew_type, sub_type, and reasoning
        """
        chain = self.prompt | self.llm | self.parser

        result = chain.invoke({
            "crew_descriptions": self.CREW_DESCRIPTIONS,
            "format_instructions": self.parser.get_format_instructions(),
            "user_request": user_request
        })

        return result

    def get_crew_config(self, user_request: str) -> Dict[str, Any]:
        """
        Get complete crew configuration including type and parameters.

        Args:
            user_request: The user's input message/query

        Returns:
            Dictionary with crew_type, sub_type, and reasoning
        """
        selection = self.select_crew(user_request)

        return {
            "crew_type": selection.crew_type,
            "sub_type": selection.sub_type,
            "reasoning": selection.reasoning
        }


def select_crew_for_task(user_request: str, llm: ChatOpenAI = None) -> Dict[str, Any]:
    """
    Convenience function to select a crew for a given task.

    Args:
        user_request: The user's input message/query
        llm: Optional language model to use

    Returns:
        Dictionary with crew_type, sub_type, and reasoning
    """
    selector = CrewSelector(llm=llm)
    return selector.get_crew_config(user_request)
