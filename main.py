"""Unified entry point for the EAGv3 Ecosystem.

Starts the LLM Gateway as a background process, waits for health check,
and then executes the iterative Agentic loop.
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from agentic.agent import Agent

GATEWAY_URL = os.getenv("LLM_GATEWAY_V3_URL", "http://localhost:8101")
GATEWAY_DIR = ROOT_DIR / "llm_gatewayV3"
PARAM_FILE = ROOT_DIR / "parameter.yaml"


def load_parameters():
    """Loads configuration from parameter.yaml."""
    if not PARAM_FILE.exists():
        print(f" [Warning] {PARAM_FILE} not found. Using defaults.")
        return {
            "query": "Hello",
            "perception": {"provider": "openrouter"},
            "decision": {"provider": "openrouter"},
        }
    with open(PARAM_FILE, "r") as f:
        return yaml.safe_load(f)


async def is_gateway_ready() -> bool:
    """Checks if the LLM Gateway is responsive and healthy."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{GATEWAY_URL}/v1/status", timeout=1.0)
            return response.status_code == 200
        except Exception:
            return False


def start_gateway():
    """Starts the LLM Gateway V3 as a background subprocess."""
    print(f" [System] Starting LLM Gateway V3 from {GATEWAY_DIR}...")

    # Use the venv python if available, otherwise fallback to system python
    venv_python = GATEWAY_DIR / ".venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    # Start uvicorn as a background process
    # We use -u for unbuffered output to see logs in real-time
    process = subprocess.Popen(
        [python_exec, "-u", "main.py"],
        cwd=str(GATEWAY_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return process


async def main():
    """Main orchestration sequence."""
    gateway_proc = None

    # 1. Check if gateway is already running
    if await is_gateway_ready():
        print(f" [System] Gateway already detected at {GATEWAY_URL}.")
    else:
        # 2. Start it if not
        gateway_proc = start_gateway()

        # 3. Wait for health check (max 30 seconds)
        print(" [System] Waiting for Gateway to initialize...", end="", flush=True)
        retries = 30
        ready = False
        while retries > 0:
            if await is_gateway_ready():
                ready = True
                break
            print(".", end="", flush=True)
            await asyncio.sleep(1.0)
            retries -= 1

        if not ready:
            print("\n [Error] Gateway failed to start within 30s. Aborting.")
            if gateway_proc:
                gateway_proc.terminate()
            return
        print(" [Ready]")

    try:
        # 4. Load Parameters
        params = load_parameters()
        query = params.get("query", "Hello")
        p_provider = params.get("perception", {}).get("provider", "openrouter")
        d_provider = params.get("decision", {}).get("provider", "openrouter")

        print("\n" + "=" * 60)
        print("  EAGv3 AGENTIC ORCHESTRATOR ACTIVE")
        print(f"  Perception: {p_provider} | Decision: {d_provider}")
        print("=" * 60)

        agent = Agent(perception_provider=p_provider, decision_provider=d_provider)
        result = await agent.run(query)

        print("\n" + "=" * 60)
        print("  FINAL AGENT RESPONSE")
        print("=" * 60)
        if not result or not str(result).strip():
            print("[Warning] Final response was empty. The Perception layer did not return a summary.")
            print("[Hint] Check the raw Perception response logs above for why the final output is blank.")
        else:
            print(result)

    finally:
        # 5. Optional: Clean up gateway if we started it
        # You might want to keep it running, but for a one-off script we terminate.
        if gateway_proc:
            print("\n [System] Terminating background Gateway...")
            gateway_proc.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n [System] User interrupted. Exiting.")
