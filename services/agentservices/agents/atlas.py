from agents import Agent
from env import open_model
from services.agentservices.prompt import ATLAS_INSTRUCTIONS
from services.weaviate.retrieval import (
    grasp_codebase,
    grasp_file,
    grasp_func,
    search_func,
    get_callee,
    get_callers,
    find_importers
    )
from services.agentservices.git_tools import file_blame,file_history




def mapper(orch_agent):

    atlas = Agent(
        name="Atlas",
        instructions=ATLAS_INSTRUCTIONS,
        model=open_model,
        handoff_description="Hand off to Atlas to explore the codebase, understand architecture, search for code symbols, and explain how specific parts of the project work.",
        handoffs=[orch_agent],
        tools=[grasp_codebase,grasp_file,grasp_func,search_func,get_callers,get_callee,find_importers,file_blame,file_history]
    )

    return atlas