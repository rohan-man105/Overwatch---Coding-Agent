from agents import Agent
from env import open_model
from pydantic import BaseModel
from services.agentservices.prompt import VERIFIER_INSTRUCTIONS
from services.agentservices.verification import run_verification
from typing import Literal


class VerificationResult(BaseModel):
    command: list[str]
    status: Literal[
        "passed",
        "failed",
        "skipped",
        "unavailable",
        "timed_out",
    ]
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    explanation: str


class VerifierOutput(BaseModel):
    summary: str
    overall_status: Literal[
        "verified",
        "failed",
        "partially_verified",
        "not_verified",
    ]
    results: list[VerificationResult]
    recommendation: str



def verify(orch_agent):

    ver = Agent(
        name="Verifier",
        instructions=VERIFIER_INSTRUCTIONS,
        model=open_model,
        handoff_description=(
            "Hand off to Verifier to compile changed Python files or run approved "
            "pytest checks, then report the actual result."
        ),
        handoffs=[orch_agent],
        tools=[run_verification],
        # output_type=VerifierOutput
    )

    return ver

