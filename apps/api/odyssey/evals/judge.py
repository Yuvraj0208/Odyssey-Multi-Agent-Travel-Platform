"""LLM-as-judge: subjective scoring against a rubric. Degrades to None if the LLM
is unavailable, so the deterministic checks can still run."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from odyssey.agents.base import safe_structured
from odyssey.providers.llm_provider import get_chat_model

_RUBRIC = """You are grading a travel itinerary against the traveler's request.
Score each dimension 1-5 (5 best):
- relevance: matches the stated interests, pace, and budget
- feasibility: realistic timing and geography for the days
- specificity: names real, specific places (not vague filler)
- overall: your holistic rating
Return the scores and a one-line comment."""

_SUPPORT_RUBRIC = """You are grading a travel-support reply for helpfulness.
Score 1-5: accuracy (grounded in the trip), helpfulness, and tone. Return scores + a comment."""


class ItineraryScore(BaseModel):
    relevance: int = Field(ge=1, le=5)
    feasibility: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    overall: int = Field(ge=1, le=5)
    comment: str = ""


async def judge_itinerary(brief: dict, itinerary: dict) -> ItineraryScore | None:
    payload = f"Traveler request: {brief}\n\nItinerary produced:\n{itinerary}"
    return await safe_structured(
        get_chat_model(),
        ItineraryScore,
        [SystemMessage(content=_RUBRIC), HumanMessage(content=payload)],
        agent="eval_judge",
    )


class SupportScore(BaseModel):
    accuracy: int = Field(ge=1, le=5)
    helpfulness: int = Field(ge=1, le=5)
    tone: int = Field(ge=1, le=5)
    comment: str = ""


async def judge_support(question: str, answer: str, context: str) -> SupportScore | None:
    payload = f"Trip context: {context}\n\nTraveler asked: {question}\n\nAgent replied: {answer}"
    return await safe_structured(
        get_chat_model(),
        SupportScore,
        [SystemMessage(content=_SUPPORT_RUBRIC), HumanMessage(content=payload)],
        agent="eval_judge",
    )
