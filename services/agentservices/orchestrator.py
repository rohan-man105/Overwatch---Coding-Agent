from agents import Agent
from env import open_model
from services.agentservices.prompt import ORCHESTRATOR_INSTRUCTIONS
from services.weaviate.retrieval import get_project_structure


def orchestrator():

    orch = Agent(
        name="Orchestrator",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        model=open_model,
        handoff_description="Hand off back to the Orchestrator when your specialized task is complete, or when you need to delegate a task outside of your expertise.",
        handoffs=[],
        tools=[get_project_structure]
    )

    from services.agentservices.atlas import mapper
    from services.agentservices.patcher import debugger


    atlas_agent = mapper(orch)
    patcher_agent = debugger(orch)


    orch.handoffs = [atlas_agent, patcher_agent]


    return orch