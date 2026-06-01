"""Pydantic schemas for the agentic module.

This module defines the data contracts used between the different cognitive
layers (Perception, Memory, Decision, Action).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Goal(BaseModel):
    """
    Represents a specific objective within a larger user query.

    Attributes:
        description (str): A clear description of what needs to be accomplished.
        is_done (bool): Flag indicating if the goal has been satisfied.
        artifact_path (Optional[str]): Path to the raw data file if the goal
            involved a tool execution.
    """

    description: str = Field(alias="goal", description="What needs to be accomplished")
    is_done: bool = Field(
        default=False, description="Whether this goal has been satisfied"
    )
    artifact_path: Optional[str] = Field(
        default=None,
        description="Path to the raw data file if this goal involved a tool",
    )

    model_config = ConfigDict(populate_by_name=True)


class MemoryKind(str, Enum):
    """Enumeration of the types of information stored in memory."""

    FACT = "fact"
    PREFERENCE = "preference"
    TOOL_OUTCOME = "tool_outcome"
    SCRATCHPAD = "scratchpad"


class MemoryItem(BaseModel):
    """
    A single categorized item stored in the agent's memory.

    Attributes:
        kind (Literal): The category of the memory (fact, preference, etc.).
        content (str): The actual information or observation.
        timestamp (str): ISO formatted timestamp of when the item was recorded.
    """

    kind: Literal["fact", "preference", "tool_outcome", "scratchpad"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PerceptionResult(BaseModel):
    """
    Output of the Perception layer after processing the current state.

    Attributes:
        goals (List[Goal]): The current list of goals and their statuses.
        context_summary (str): A brief summary of the current session state or
            the final answer if all goals are complete.
        relevant_artifacts (List[str]): Paths to all artifacts relevant to the session.
        new_knowledge (List[MemoryItem]): New facts or preferences discovered.
    """

    goals: List[Goal] = Field(
        alias="goal_list", description="The current list of goals and their status"
    )
    context_summary: str = Field(
        default="", description="Brief summary of the current session state"
    )
    relevant_artifacts: List[str] = Field(
        default_factory=list,
        description="List of all artifact paths relevant to the current session",
    )
    new_knowledge: List[MemoryItem] = Field(
        alias="knowledge",
        default_factory=list,
        description="New facts or preferences discovered during this perception step",
    )

    model_config = ConfigDict(populate_by_name=True)


class ToolCall(BaseModel):
    """
    A request to execute a specific MCP tool.

    Attributes:
        name (str): The name of the tool to call.
        arguments (Dict[str, Any]): The arguments to pass to the tool function.
    """

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class FinalAnswer(BaseModel):
    """
    Internal model representing a final text response.

    Attributes:
        text (str): The final answer text.
    """

    text: str


class DecisionResult(BaseModel):
    """
    Output of the Decision layer choosing the next logical action.

    Attributes:
        tool_call (Optional[ToolCall]): The tool to execute, if any.
        final_answer (Optional[str]): The final answer string, if satisfied.
        thought (str): Internal reasoning behind the chosen action.
    """

    tool_call: Optional[ToolCall] = Field(
        default=None, description="Request to run a tool"
    )
    final_answer: Optional[str] = Field(
        default=None, description="Final answer to the user as a plain string"
    )
    thought: str = Field(
        default="", description="The reasoning behind picking this action"
    )


class MemoryArtifact(BaseModel):
    """
    Consolidated structure of the agent's memory for a session.

    Attributes:
        items (List[MemoryItem]): Chronological list of all memory items.
        last_updated (str): ISO formatted timestamp of the last update.
    """

    items: List[MemoryItem] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class ActionResponse(BaseModel):
    """
    The result of executing an action.

    Attributes:
        status (Literal): Whether the execution succeeded or failed.
        output_summary (str): A short description of the result for Memory.
        artifact_path (Optional[str]): Path where full raw output is stored.
        raw_output (Optional[Any]): The actual raw data returned by the tool.
    """

    status: Literal["success", "failure"]
    output_summary: str = Field(
        description="Short descriptor of what happened for Memory"
    )
    artifact_path: Optional[str] = None
    raw_output: Optional[Any] = None
