from agents import Agent
from env import open_model
from pydantic import BaseModel


class VerifierOutput(BaseModel):
    pass



def verifier():

    ver = Agent(
        name="Verifier",
        instructions="",
        model=open_model,
        handoff_description="",
        handoffs=[],
        output_type=VerifierOutput
    )

    return ver

