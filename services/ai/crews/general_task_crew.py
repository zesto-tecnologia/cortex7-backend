"""
General task crew for versatile workflows.
"""

from crewai import Crew, Task
from ..agents.domain.financial_agent import create_financial_agent
from ..agents.domain.hr_agent import create_hr_agent
from ..agents.domain.legal_agent import create_legal_agent
from ..agents.domain.documents_agent import create_documents_agent
from ..agents.domain.procurement_agent import create_procurement_agent
from ..agents.general.researcher_agent import create_researcher_agent
from ..agents.general.analyst_agent import create_analyst_agent
from ..agents.general.writer_agent import create_writer_agent


def create_general_task_crew(llm, empresa_id: str, task_description: str):
    """
    Create a versatile crew that can handle general business tasks.
    
    Dynamically selects agents based on task description keywords.
    
    Args:
        llm: Language model to use
        empresa_id: Company UUID
        task_description: Description of the task to perform
    """
    # Initialize all domain agents
    all_agents = {
        "financial": create_financial_agent(llm),
        "hr": create_hr_agent(llm),
        "legal": create_legal_agent(llm),
        "documents": create_documents_agent(llm),
        "procurement": create_procurement_agent(llm),
        "researcher": create_researcher_agent(llm),
        "analyst": create_analyst_agent(llm),
        "writer": create_writer_agent(llm),
    }
    
    # Determine which agents to use based on task description
    task_lower = task_description.lower()
    selected_agents = []
    
    # Domain-specific agent selection
    if any(word in task_lower for word in ["financial", "payment", "invoice", "supplier", "cost"]):
        selected_agents.append(all_agents["financial"])
    
    if any(word in task_lower for word in ["employee", "hr", "vacation", "contract", "staff"]):
        selected_agents.append(all_agents["hr"])
    
    if any(word in task_lower for word in ["legal", "contract", "deadline", "process", "lawsuit"]):
        selected_agents.append(all_agents["legal"])
    
    if any(word in task_lower for word in ["document", "file", "search", "report"]):
        selected_agents.append(all_agents["documents"])
    
    if any(word in task_lower for word in ["purchase", "procurement", "order", "approval"]):
        selected_agents.append(all_agents["procurement"])
    
    # Always include general agents for versatility
    if not selected_agents:
        selected_agents.append(all_agents["researcher"])
    
    selected_agents.append(all_agents["analyst"])
    selected_agents.append(all_agents["writer"])
    
    # Create main task
    main_task = Task(
        description=f"For company {empresa_id}: {task_description}. Gather all necessary information and provide a comprehensive response.",
        agent=selected_agents[0],
        expected_output="Complete information and initial findings"
    )
    
    # Analysis task
    analysis_task = Task(
        description="Analyze the gathered information and provide insights, recommendations, and actionable steps.",
        agent=all_agents["analyst"],
        expected_output="Analysis with insights and recommendations",
        context=[main_task]
    )
    
    # Final report task
    report_task = Task(
        description="Create a clear, professional response that addresses the original request comprehensively.",
        agent=all_agents["writer"],
        expected_output="Professional, well-structured response",
        context=[main_task, analysis_task]
    )
    
    crew = Crew(
        agents=selected_agents,
        tasks=[main_task, analysis_task, report_task],
        verbose=True,
    )
    
    return crew

