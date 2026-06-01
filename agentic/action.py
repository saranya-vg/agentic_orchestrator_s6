"""Action service for the agentic module.

This module handles the execution of MCP tools and the management of
tool-specific artifacts. It provides a bridge between the cognitive
Decision layer and the physical tool environment.
"""

import asyncio
from typing import Any, Dict, Optional

from agentic.memory import ArtifactStorage
from agentic.schemas import ActionResponse, ToolCall


class Action:
    """
    Dispatcher and executor for MCP tools.

    Handles tool discovery, asynchronous execution, and raw data persistence
    using ArtifactStorage.
    """

    def __init__(self, storage: ArtifactStorage):
        self.storage = storage

    async def execute(self, tool_call: ToolCall) -> ActionResponse:
        """
        Executes a specific tool call and records the outcome.

        Args:
            tool_call (ToolCall): The tool name and arguments.

        Returns:
            ActionResponse: Status, raw output, and a short summary.
        """
        print(f"  >> Executing [{tool_call.name}]...")

        # Real MCP tool discovery and execution
        try:
            from mcp_server import mcp

            # Find the tool in the manager
            tool = next(
                (t for t in mcp._tool_manager.list_tools() if t.name == tool_call.name),
                None,
            )
            if not tool:
                return ActionResponse(
                    status="failure",
                    output_summary=f"Tool '{tool_call.name}' not found.",
                )

            # Execute (handles both sync and async tools)
            raw_res = tool.fn(**tool_call.arguments)
            if asyncio.iscoroutine(raw_res):
                raw_res = await raw_res

            # Save raw output to artifact store
            path = self.storage.save(f"raw_output_{tool_call.name}", raw_res)

            # Create short descriptor for memory
            # Use sandbox-relative path for tool outcomes so read_file works correctly
            rel_path = f"artifacts/{path.name}"
            content_snippet = ""
            if isinstance(raw_res, (str, list, dict)):
                raw_str = str(raw_res)
                content_snippet = (
                    f"\nContent Snippet (first 1000 chars): {raw_str[:1000]}..."
                )

            summary = (
                f"Executed {tool_call.name}. Result length: {len(str(raw_res))} chars. "
                f"Full result stored in {rel_path}.{content_snippet}"
            )

            return ActionResponse(
                status="success",
                output_summary=summary,
                artifact_path=str(path),
                raw_output=raw_res,
            )
        except Exception as e:
            print(f" [Action] Exception executing {tool_call.name}: {e}")
            return ActionResponse(
                status="failure", output_summary=f"Execution error: {e}"
            )
