"""
General task crew for versatile workflows.
"""

from crewai import Crew, Task
from ..agents.domain.financial_agent import create_financial_agent
from ..agents.domain.hr_agent import create_hr_agent
from ..agents.domain.legal_agent import create_legal_agent
from ..agents.domain.documents_agent import create_documents_agent
from ..agents.domain.procurement_agent import create_procurement_agent
from ..agents.domain.pipefy_agent import create_pipefy_agent
from ..agents.general.researcher_agent import create_researcher_agent
from ..agents.general.analyst_agent import create_analyst_agent
from ..agents.general.writer_agent import create_writer_agent


def generate_flow_diagram(agents, tasks):
    """
    Generate a simple ASCII flow diagram showing the agent and task flow.

    Args:
        agents: List of agents used in the crew
        tasks: List of tasks in the crew

    Returns:
        String containing the flow diagram
    """
    diagram_lines = ["\n", "=" * 60, "FLUXO DE EXECUÇÃO / EXECUTION FLOW", "=" * 60, "\n"]

    # Get agent names
    agent_names = []
    for agent in agents:
        # Extract role from agent
        role = getattr(agent, 'role', 'Unknown Agent')
        agent_names.append(role)

    # Build the flow
    diagram_lines.append("AGENTES / AGENTS:")
    for i, agent_name in enumerate(agent_names, 1):
        diagram_lines.append(f"  {i}. {agent_name}")

    diagram_lines.append("\nTAREFAS / TASKS:")
    for i, task in enumerate(tasks, 1):
        task_agent = getattr(task, 'agent', None)
        agent_role = getattr(task_agent, 'role', 'Unknown') if task_agent else 'Unknown'
        diagram_lines.append(f"  {i}. {agent_role}")

    # Create flow visualization
    diagram_lines.append("\nFLUXO / FLOW:")
    flow = " -> ".join([getattr(task.agent, 'role', 'Unknown') for task in tasks])
    diagram_lines.append(f"  {flow}")

    diagram_lines.append("\n" + "=" * 60)

    return "\n".join(diagram_lines)


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
        "pipefy": create_pipefy_agent(llm),
        "researcher": create_researcher_agent(llm),
        "analyst": create_analyst_agent(llm),
        "writer": create_writer_agent(llm),
    }
    
    # Determine which agents to use based on task description
    task_lower = task_description.lower()
    selected_agents = []
    
    # Domain-specific agent selection (Portuguese and English keywords)
    if any(word in task_lower for word in ["financial", "payment", "invoice", "supplier", "cost",
                                             "financeiro", "pagamento", "fatura", "fornecedor", "custo"]):
        selected_agents.append(all_agents["financial"])

    if any(word in task_lower for word in ["employee", "hr", "vacation", "contract", "staff",
                                             "funcionário", "funcionario", "rh", "férias", "ferias", "contrato", "equipe"]):
        selected_agents.append(all_agents["hr"])

    if any(word in task_lower for word in ["legal", "contract", "deadline", "process", "lawsuit",
                                             "jurídico", "juridico", "contrato", "prazo", "processo", "ação"]):
        selected_agents.append(all_agents["legal"])

    if any(word in task_lower for word in ["document", "file", "search", "report",
                                             "documento", "arquivo", "busca", "relatório", "relatorio"]):
        selected_agents.append(all_agents["documents"])

    if any(word in task_lower for word in ["purchase", "procurement", "order", "approval",
                                             "compra", "aquisição", "aquisicao", "pedido", "aprovação", "aprovacao", "fornecedor"]):
        selected_agents.append(all_agents["procurement"])

    if any(word in task_lower for word in ["pipefy", "pipe", "card", "workflow", "process", "phase",
                                             "cartão", "cartao", "fluxo", "processo", "fase", "etapa"]):
        selected_agents.append(all_agents["pipefy"])

    # Always include general agents for versatility
    if not selected_agents:
        selected_agents.append(all_agents["researcher"])
    
    # selected_agents.append(all_agents["analyst"])
    # selected_agents.append(all_agents["writer"])
    
    # Create main task
    main_task = Task(
        description=f"Para a empresa {empresa_id}: {task_description}. Reúna todas as informações necessárias e forneça uma resposta abrangente em português brasileiro.",
        agent=selected_agents[0],
        expected_output="Informações completas e descobertas iniciais em português brasileiro"
    )

    # Analysis task
    analysis_task = Task(
        description="Analise as informações coletadas e forneça insights, recomendações e passos acionáveis em português brasileiro.",
        agent=all_agents["analyst"],
        expected_output="Análise com insights e recomendações em português brasileiro",
        context=[main_task]
    )

    # Final report task
    report_task = Task(
        description="Crie uma resposta clara e profissional que atenda à solicitação original de forma abrangente em português brasileiro.",
        agent=all_agents["writer"],
        expected_output="Resposta profissional e bem estruturada em português brasileiro",
        context=[main_task, analysis_task]
    )
    
    # Store all agents and tasks for diagram generation
    all_tasks = [main_task, analysis_task, report_task]

    crew = Crew(
        agents=selected_agents + [all_agents["analyst"], all_agents["writer"]],
        tasks=all_tasks,
        verbose=True,
    )

    # Store the diagram information in the crew object for later use
    crew._flow_diagram = generate_flow_diagram(
        selected_agents + [all_agents["analyst"], all_agents["writer"]],
        all_tasks
    )

    return crew

