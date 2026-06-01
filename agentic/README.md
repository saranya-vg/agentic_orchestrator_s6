# Agentic Module

An implementation of an **iterative, goal-driven cognitive loop** based on the Axiom architecture. This module coordinates Perception, Memory, Decision, and Action layers to resolve complex user queries through automated research and tool execution.

## 🏗 Architecture

The module is divided into four distinct cognitive services:

1.  **Perception (Orchestrator)**: Manages the **Goal List**. It breaks queries into logical steps and evaluates progress based on memory. It also extracts durable knowledge (facts/preferences).
2.  **Memory (State)**: A pure service for storing and reading categorized information. It manages durable state (archived on disk) and transient session outcomes.
3.  **Decision (Action Selection)**: Picks the single next logical action (tool call or final answer) for the current goal, prioritizing local knowledge before external tools.
4.  **Action (Dispatch)**: Executes MCP tools asynchronously and manages the storage of raw data artifacts.

## 📂 Module Structure

```text
agentic/
├── agent.py        # The Core Orchestrator (Iterative Loop)
├── perception.py   # Goal management & knowledge extraction
├── decision.py     # Single-step action selection
├── memory.py       # Categorized storage & durable state
├── action.py       # Asynchronous MCP tool execution
├── schemas.py      # Pydantic data contracts (Type safety)
└── artifacts/      # (Auto-generated) JSON state and raw data
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A running **LLM Gateway V3** on port 8101.
- MCP Server tools configured in `mcp_server.py`.

### Usage

```python
import asyncio
from agentic.agent import Agent

async def main():
    agent = Agent()
    result = await agent.run("Find information about SpaceX's Starship and save it to a file.")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧠 Memory Kinds

The module implements a four-tier memory system:

| Kind | Description | Persistence |
| :--- | :--- | :--- |
| `fact` | Durable observed truths. | **Disk** (`/state/`) |
| `preference` | User-stated or inferred preferences. | **Disk** (`/state/`) |
| `tool_outcome` | Record of one MCP tool dispatch. | Session Only |
| `scratchpad` | Intermediate reasoning/working notes. | Run Only |

## 🛠 Features

- **PEP 257 Compliant**: All functions and classes are fully documented.
- **Type Safety**: Built with **Pydantic v2** for strict data validation.
- **Cross-Session Memory**: Automatically reloads facts and preferences from previous runs.
- **Resilient Orchestration**: Handles LLM failures with graceful fallbacks.
- **Artifact Traceability**: Every tool execution saves a raw JSON artifact for full observability.
