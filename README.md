# EAGv3: Iterative Cognitive Agent Ecosystem

A robust, self-improving AI ecosystem built on the **Axiom Architecture**. This project coordinates an intelligent agentic loop, a capability-aware routing gateway, and a versatile tool server.

## 🏗 System Architecture

The ecosystem consists of three primary layers:

1.  **Agentic Module (`/agentic`)**: The cognitive core. Implements an iterative **Perception-Memory-Decision-Action** loop. It manages goals, extracts durable knowledge, and plans tool usage.
2.  **LLM Gateway V3 (`/llm_gatewayV3`)**: The routing backbone. A FastAPI service that routes requests across multiple providers (OpenAI, Gemini, Groq, etc.) with automatic failover and cognitive-layer routing.
3.  **MCP Server (`mcp_server.py`)**: The tool repository. Provides the agent with "hands" to interact with the world (web search, browser fetching, file operations, etc.) via the Model Context Protocol.

---

## 📂 Project Structure

```text
.
├── agentic/            # Iterative Agentic Loop (Perception, Memory, Decision, Action)
├── llm_gatewayV3/      # Smart Routing Gateway (Multi-provider, RPM/TPM management)
├── sandbox/            # Secure environment for agent file operations
│   └── artifacts/      # JSON state, durable facts, and tool outputs
├── mcp_server.py       # Model Context Protocol tool definitions
├── main.py             # Simple entry point for gateway testing
└── .env                # Environment secrets (API Keys)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- pip install requirements.txt inside llm_gatewayV3 and root

### 2. Configuration
Create a `.env` file in the root directory:
```env
OPEN_ROUTER_API_KEY=your_key
TAVILY_API_KEY=your_key (for web search)
# See .env.example for more provider keys
```

### 3. Configuration
1. **Secrets**: Create a `.env` file in the root directory:
```env
OPEN_ROUTER_API_KEY=your_key
TAVILY_API_KEY=your_key (for web search)
# See .env.example for more provider keys
```

2. **Parameters**: Modify `parameter.yaml` to set your query and choose providers for each cognitive layer:
```yaml
query: "Search for today's top tech news."
perception:
  provider: "openai"
decision:
  provider: "openai"
```

### 4. Run the Application
You can run the entire ecosystem with a single command from the root directory. This will start the LLM Gateway, wait for it to be ready, and then trigger the agent:

```bash
python main.py
```

---

## 📖 Example Run Logs

Below are real examples of the agent resolving different types of queries using its iterative loop and durable memory.

### 1. Complex Fact Extraction (Web Research)
**Query**: *"Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory."*
```text
--- Iteration 1 ---
 [Perception] All goals satisfied.

============================================================
  FINAL AGENT RESPONSE
============================================================
Claude Shannon was born on April 30, 1916, and died on February 24, 2001. His three key contributions to information theory are: 1) Founding information theory and introducing the concept of the bit as a unit of information, 2) Developing the Shannon entropy formula...
```

### 2. Multi-Goal Orchestration (Search + Weather + Reasoning)
**Query**: *"Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one is most appropriate."*
```text
--- Iteration 1 ---
 [Perception] Current Goal: Find 3 family-friendly things to do in Tokyo this weekend
 [Decision] Thought: I need to find 3 family-friendly activities in Tokyo...
  >> Executing [web_search]...
 [Action] Result: success

--- Iteration 2 ---
 [Perception] Current Goal: Check Saturday's weather forecast in Tokyo
  >> Executing [web_search]...
 [Action] Result: success

--- Iteration 5 ---
 [Perception] All goals satisfied.

============================================================
  FINAL AGENT RESPONSE
============================================================
We have identified three family-friendly activities... The Saturday weather forecast is cloudy with a 20-30% chance of rain. Considering the weather, the most appropriate activity is visiting the Ghibli Museum since it is an indoor activity.
```

### 3. Knowledge Extraction (Creating a Durable Fact)
**Query**: *"My mom's birthday is 15 May 2026. Remember that and give me a calendar reminder for two weeks before and on the day."*
```text
--- Iteration 1 ---
 [Perception] Discovered fact: User's mom's birthday is May 15, 2026.
 [Perception] Discovered fact: Calendar reminder set for May 1, 2026...
 [Perception] All goals satisfied.

============================================================
  FINAL AGENT RESPONSE
============================================================
The user's mom's birthday is remembered as May 15, 2026. Calendar reminders have been created...
```

### 4. Cross-Session Memory (Retrieving a Stored Fact)
**Query**: *"When is my mom's birthday?"*
```text
--- Iteration 1 ---
 [Perception] All goals satisfied.

============================================================
  FINAL AGENT RESPONSE
============================================================
The user's mom's birthday is on May 15, 2026. Calendar reminders have been set for May 1, 2026 and May 15, 2026.
```

---

## 🧠 Component Deep Dives

### [Agentic Module](./agentic/README.md)
The agent follows the **Axiom pattern**:
- **Perception**: Evaluates state and manages the goal list (Orchestrator).
- **Memory**: Stores durable facts/preferences in `/sandbox/artifacts/state/`.
- **Decision**: Selects the next tool call or provides the final answer.
- **Action**: Dispatches tools to the MCP server.

### [LLM Gateway V3](./llm_gatewayV3/README.md)
A high-performance router designed for agentic workloads:
- **Cognitive Routing**: Automatically routes based on `perception`, `memory`, or `decision` requirements.
- **Failover**: If OpenAI is down or rate-limited, it automatically falls back to Gemini, Groq, or others.
- **Schema Validation**: Ensures all LLM outputs strictly match the Pydantic models defined in the agent.

### MCP Server
Exposes a suite of tools to the agent:
- `web_search`: Multi-engine search for information gathering.
- `fetch_url`: Full-page markdown extraction via headless browser (`crawl4ai`).
- `read_file` / `create_file`: Sandbox-safe filesystem operations.
- `read_durable_state`: Direct access to the agent's long-term memory.

---

## 🛠 Features
- **Cross-Session Memory**: Facts learned today are available tomorrow.
- **Production-Ready**: Built with Pydantic v2 and FastAPI.
- **Type Safe**: Strict data contracts between all cognitive layers.
- **Observability**: Every action is saved as a JSON artifact for debugging.
