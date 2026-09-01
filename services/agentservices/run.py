from agents import Runner
import asyncio
from agents.stream_events import (
    AgentUpdatedStreamEvent,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
)
from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent
from services.agentservices.agents.orchestrator import orchestrator
import sys



default_agent = orchestrator()




async def run_agents(user_input:str,history:list,curr_agent=None):

    if curr_agent == None:
        curr_agent = default_agent

    if user_input:
        history.append({
            "role" : "user",
            "content" : user_input
        })

    response = Runner.run_streamed(curr_agent, input=history)
    full_text=[]

    async for event in response.stream_events():
        
        if isinstance(event, RawResponsesStreamEvent):
            if isinstance(event.data, ResponseTextDeltaEvent) and event.data.delta:
                sys.stdout.write(event.data.delta)
                sys.stdout.flush()
                full_text.append(event.data.delta)
                
        elif isinstance(event, RunItemStreamEvent):
            if event.item.type == "tool_call_item":
                name = getattr(event.item, "name", getattr(event.item, "tool_name", "unknown"))
                sys.stdout.write(f"\n*[Calling tool: {name}...]*\n")
                sys.stdout.flush()
                
        elif isinstance(event, AgentUpdatedStreamEvent):
            sys.stdout.write(f"\n*[Handed off to {event.new_agent.name}...]*\n")
            sys.stdout.flush()

    
    history.clear()
    history.extend(response.to_input_list())  
    final_text = "".join(full_text).strip()

    print() 
    return response,final_text