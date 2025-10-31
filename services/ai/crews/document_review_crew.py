"""
Document review crew for document analysis workflows.
"""

from crewai import Crew, Task
from ..agents.domain.documents_agent import create_documents_agent
from ..agents.general.analyst_agent import create_analyst_agent
from ..agents.general.writer_agent import create_writer_agent


def create_document_review_crew(llm, company_id: str, query: str, review_type: str = "general"):
    """
    Create a crew for document review and analysis.
    
    Args:
        llm: Language model to use
        company_id: Company UUID
        query: Search query or topic for document review
        review_type: Type of review ('general', 'compliance', 'summary')
    """
    documents_agent = create_documents_agent(llm)
    analyst_agent = create_analyst_agent(llm)
    writer_agent = create_writer_agent(llm)
    
    # Search and retrieve documents
    search_task = Task(
        description=f"Search and retrieve relevant documents for company {company_id} related to: '{query}'. Gather all pertinent information.",
        agent=documents_agent,
        expected_output="List of relevant documents with their content and metadata"
    )
    
    # Analyze documents
    if review_type == "compliance":
        analysis_task = Task(
            description="Review the documents for compliance issues, missing information, and potential risks. Identify any red flags.",
            agent=analyst_agent,
            expected_output="Compliance analysis with identified issues and risk assessment",
            context=[search_task]
        )
    elif review_type == "summary":
        analysis_task = Task(
            description="Analyze and summarize the key points, themes, and important information from the documents.",
            agent=analyst_agent,
            expected_output="Comprehensive summary of document contents with key insights",
            context=[search_task]
        )
    else:  # general
        analysis_task = Task(
            description="Analyze the documents to extract insights, patterns, and actionable information.",
            agent=analyst_agent,
            expected_output="Document analysis with insights and recommendations",
            context=[search_task]
        )
    
    # Create final report
    report_task = Task(
        description="Create a clear, well-structured report presenting the findings in a professional format.",
        agent=writer_agent,
        expected_output="Professional report summarizing document review findings",
        context=[search_task, analysis_task]
    )
    
    crew = Crew(
        agents=[documents_agent, analyst_agent, writer_agent],
        tasks=[search_task, analysis_task, report_task],
        verbose=True,
    )
    
    return crew
