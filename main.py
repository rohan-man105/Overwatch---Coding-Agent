import asyncio
from services.weaviate.load import embed
from services.agentservices.run import run_agents
from agents import set_tracing_disabled
from services.weaviate import utils

set_tracing_disabled(True)

async def main():
    
   
    client_path = input("Enter the project path to analyze: ")
    
    utils.url = client_path
    embed(client_path)

    history = []
    curr_agent = None

    while(True):

        user_input = input("\nYOU: ")

        if user_input.lower() in ["exit","quit"]:
            break

        result,final_reply = await run_agents(user_input,history,curr_agent)
        curr_agent = result.last_agent


if __name__ == "__main__":
    asyncio.run(main())        




