"""Perception service for the agentic module.

This module acts as the orchestrator for the cognitive loop. It breaks down
user queries into discrete goals and evaluates when those goals have been
satisfied based on memory and action history.
"""

import json
from typing import Dict, List, Optional

from pydantic import ValidationError

from agentic.schemas import Goal, MemoryItem, PerceptionResult
from llm_gatewayV3.client import LLM


class Perception:
    """
    The orchestrator of the cognitive cycle.

    Responsible for goal management, knowledge extraction, and high-level
    state summarization using the LLM.
    """

    def __init__(self, llm: LLM, provider: str = "openrouter"):
        self.llm = llm
        self.provider = provider

    def process(
        self, query: str, memory_context: str, run_history: List[str] = None
    ) -> PerceptionResult:
        """
        Processes the current state to update goals and extract knowledge.

        Args:
            query (str): The original user query.
            memory_context (str): Categorized memory content from the Memory service.
            run_history (Optional[List[str]]): Chronological thoughts and action
                summaries from the current loop execution.

        Returns:
            PerceptionResult: Updated goal list and discovered facts/preferences.
        """
        history_str = ""
        if run_history:
            history_str = "\nCHRONOLOGICAL RUN HISTORY:\n- " + "\n- ".join(run_history)

        prompt = (
            f"USER QUERY: {query}\n\n"
            f"{history_str}\n\n"
            f"CURRENT CATEGORIZED MEMORY:\n{memory_context}"
        )

        try:
            # Using gpt-4.1-mini tier for better orchestration and goal evaluation.
            result = self.llm.chat(
                prompt=prompt,
                system=(
                    "You are the Perception layer (The Orchestrator). Your job is to manage the GOAL LIST, extract KNOWLEDGE, and summarize STATE.\n\n"
                    "GOAL RULES:\n"
                    "1. Break the query into logical steps (Goals). Use the 'goals' property for the list.\n"
                    "2. REVIEW THE MEMORY: If a tool output provides information for a goal, mark it 'is_done': true.\n"
                    "3. TRACK ARTIFACTS: Identify the exact 'artifacts/...' relative path from the Memory for each completed goal and include it in the 'artifact_path' field.\n\n"
                    "KNOWLEDGE & STATE RULES:\n"
                    "1. TERMINATION: If the information in Memory fully satisfies the USER QUERY, you MUST mark all goals 'is_done': true and do NOT create any new goals. This is the signal that the session is complete.\n"
                    "2. FINAL ANSWER: When all goals are done, you MUST provide the final, comprehensive answer to the user in the 'context_summary' field.\n"
                    "3. DIRECT ANSWER PATH: If the query is directly answerable without multi-step goals, you may return an empty goal_list and MUST still put the complete answer in 'context_summary'.\n"
                    "4. FALLBACK GOAL: If you cannot identify discrete goals, create a single fallback goal representing the user's original request and set it in 'goal_list'.\n"
                    "5. DURABLE STATE SUMMARY: If goals are still pending, use 'context_summary' to summarize what we currently know about the user/session.\n"
                    "6. EXTRACTION: Identify new durable FACTS or PREFERENCES and add them to 'new_knowledge'."
                ),
                response_format={
                    "type": "json_schema",
                    "schema": PerceptionResult.model_json_schema(),
                },
                provider=self.provider,
            )
            raw_text = (result.get("text") or "").strip()
            print(f" [Perception] raw response:\n{raw_text[:1200]}")
            perception = PerceptionResult.model_validate_json(raw_text)
            if not perception.goals:
                if perception.context_summary.strip():
                    print(
                        " [Perception] No goals returned but context_summary exists; treating as a completed response."
                    )
                    perception.goals = [Goal(description=query, is_done=True)]
                else:
                    print(" [Perception] Warning: no goals extracted from model output.")
                    perception.goals = [Goal(description=query)]
                    perception.context_summary = (
                        "Perception failed to extract goals; proceeding with a fallback goal based on the original query."
                    )
            if not perception.context_summary.strip() and all(g.is_done for g in perception.goals):
                if perception.knowledge:
                    facts = ", ".join(item.content for item in perception.knowledge)
                    perception.context_summary = (
                        f"Goals completed. Extracted facts: {facts}."
                    )
                else:
                    descriptions = ", ".join(g.description for g in perception.goals)
                    perception.context_summary = (
                        f"Goals completed: {descriptions}."
                    )
            elif not perception.context_summary.strip():
                perception.context_summary = "Perception completed without a context_summary."
            return perception
        except Exception as e:
            if hasattr(e, "response") and e.response is not None:
                print(
                    f" [Error] Perception Gateway returned {e.response.status_code}: {e.response.text}"
                )
            return PerceptionResult(
                goals=[Goal(description=query)], context_summary=f"Error: {e}"
            )
