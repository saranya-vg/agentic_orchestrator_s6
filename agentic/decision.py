"""Decision service for the agentic module.

This module picks the single next action (tool call or final answer) for a
bounded goal, ensuring logical progression and avoiding redundant operations.
"""

import json
from typing import Dict, List, Optional

from agentic.schemas import DecisionResult, Goal
from llm_gatewayV3.client import LLM


class Decision:
    """
    Action selector for specific agent goals.

    Evaluates the current goal against memory and perception summaries to
    determine if a tool call is needed or if the goal can be satisfied.
    """

    def __init__(self, llm: LLM, provider: str = "openrouter"):
        self.llm = llm
        self.provider = provider

    def plan(
        self,
        goal: Goal,
        memory_context: str,
        tools: List[Dict],
        original_query: str = "",
        relevant_artifacts: List[str] = None,
        perception_summary: str = "",
    ) -> DecisionResult:
        """
        Picks the next action for a specific bounded goal.

        Args:
            goal (Goal): The specific goal being addressed in this turn.
            memory_context (str): Formatted memory content.
            tools (List[Dict]): List of available MCP tools.
            original_query (str): The full original request from the user.
            relevant_artifacts (Optional[List[str]]): List of raw data addresses.
            perception_summary (str): Reasoning and state summary from Perception.

        Returns:
            DecisionResult: The chosen tool call or final answer string.
        """
        artifacts_info = ""
        if relevant_artifacts:
            artifacts_info = (
                "Relevant Artifacts (Raw Data Addresses):\n- "
                + "\n- ".join(relevant_artifacts)
            )

        prompt = (
            f"Original User Request: {original_query}\n"
            f"Current Focused Goal: {goal.description}\n\n"
            f"PERCEPTION SUMMARY (The Orchestrator's View):\n{perception_summary}\n\n"
            f"{artifacts_info}\n\n"
            f"CURRENT CATEGORIZED MEMORY:\n{memory_context}\n\n"
            f"Available Tools:\n{json.dumps(tools, indent=2)}"
        )

        try:
            # Using gpt-4.1-mini tier for better tool selection and logic execution.
            result = self.llm.chat(
                prompt=prompt,
                system=(
                    "You are the Decision layer. Pick the NEXT ACTION for the current goal.\n\n"
                    "RULES:\n"
                    "1. LOCAL KNOWLEDGE FIRST: If the info could be personal, use 'read_durable_state' first.\n"
                    "2. ESCALATION: If local check failed, IMMEDIATELY use 'web_search' or 'fetch_url'.\n"
                    "3. ACT, DON'T CHAT: If you need a tool, you MUST return a 'tool_call'. Do NOT provide a 'final_answer' saying you will use a tool.\n"
                    "4. FORMAT: You must return valid JSON with either 'tool_call' OR 'final_answer'.\n\n"
                    "EXAMPLES:\n"
                    '- Tool Call: {"tool_call": {"name": "web_search", "arguments": {"query": "Gemini 2.0 news"}}, "thought": "Searching for recent Gemini updates."}\n'
                    '- Final Answer: {"final_answer": "The flight is at 10 AM.", "thought": "Found the time in memory."}'
                ),
                response_format={
                    "type": "json_schema",
                    "schema": DecisionResult.model_json_schema(),
                },
                provider=self.provider,
            )
            raw_text = (result.get("text") or "").strip()
            print(f" [Decision] raw response:\n{raw_text[:1200]}")
            decision = DecisionResult.model_validate_json(raw_text)

            # Prevent empty decisions
            if not decision.tool_call and not decision.final_answer:
                raise ValueError(
                    "LLM returned an empty decision (no tool_call or final_answer)"
                )

            return decision

        except Exception as e:
            if hasattr(e, "response") and e.response is not None:
                print(
                    f" [Error] Decision Gateway returned {e.response.status_code}: {e.response.text}"
                )
            return DecisionResult(
                final_answer=f"Decision Error: {e}",
                thought="Fallback due to error.",
            )
