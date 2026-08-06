from agents import Agent 
from env import open_model
from services.agentservices.prompt import PATCHER_INSTRUCTIONS
from services.weaviate.retrieval import grasp_codebase, grasp_file, grasp_func, search_func


def debugger(orch_agent):

    patch = Agent(
        name="Patcher",
        instructions=PATCHER_INSTRUCTIONS,
        model=open_model,
        handoff_description="Hand off to Patcher to debug runtime errors, analyze stack traces, fix bugs and propose code changes or refactors.",
        handoffs=[orch_agent],
        tools=[grasp_codebase, grasp_file, grasp_func, search_func]
    )

    return patch