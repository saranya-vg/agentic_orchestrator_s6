"""Memory service for the agentic module.

This module handles session state, durable knowledge (facts/preferences),
and artifact storage. It provides a pure service for reading and recording
information without LLM dependency.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentic.schemas import MemoryArtifact, MemoryItem

# Configuration
AGENTIC_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = AGENTIC_ROOT / "sandbox" / "artifacts"
STATE_DIR = ARTIFACTS_DIR / "state"

# Ensure directories exist
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)
STATE_DIR.mkdir(exist_ok=True, parents=True)


class ArtifactStorage:
    """
    Manages saving and retrieving Pydantic-validated artifacts.

    Args:
        storage_dir (Path): The filesystem directory to store artifacts in.
    """

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True, parents=True)

    def save(self, name: str, data: Any) -> Path:
        """
        Saves raw data wrapped in a metadata envelope as a JSON artifact.

        Args:
            name (str): Logical name for the artifact.
            data (Any): The payload to save.

        Returns:
            Path: The path to the created JSON file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in name])
        path = self.storage_dir / f"{timestamp}_{safe_name}.json"

        envelope = {
            "metadata": {"name": name, "timestamp": datetime.now().isoformat()},
            "payload": data,
        }
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        return path

    def sync_file(self, filename: str, data: Any) -> Path:
        """
        Overwrites or creates a specific file with JSON data.

        Used for maintaining durable state across sessions.

        Args:
            filename (str): Name of the file in the storage directory.
            data (Any): The payload to sync.

        Returns:
            Path: The path to the synced file.
        """
        path = self.storage_dir / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path


class Memory:
    """
    Categorized memory system for the agent.

    Stores facts, preferences, tool outcomes, and scratchpad entries.
    Durable knowledge (facts and preferences) is loaded from and synced to disk.
    """

    def __init__(self):
        self.artifact_store = ArtifactStorage(ARTIFACTS_DIR)
        self.state_store = ArtifactStorage(STATE_DIR)

        self.state = MemoryArtifact()
        self._load_durable_state()

    def _load_durable_state(self):
        """Loads facts and preferences from the state storage into memory."""
        durable_path = STATE_DIR / "durable_state.json"
        if durable_path.exists():
            try:
                data = json.loads(durable_path.read_text(encoding="utf-8"))
                for item_data in data:
                    item = MemoryItem.model_validate(item_data)
                    # Add to session state if not already there
                    if item.content not in [it.content for it in self.state.items]:
                        self.state.items.append(item)
            except Exception as e:
                print(f" [Warning] Could not load durable state: {e}")

    def read(self, filter_kinds: Optional[List[str]] = None) -> str:
        """
        Returns a formatted string of categorized memory items.

        Args:
            filter_kinds (Optional[List[str]]): Specific kinds of memory to return.
                Defaults to all kinds.

        Returns:
            str: A formatted block of text suitable for an LLM prompt.
        """
        if not self.state.items:
            return "No prior history."

        output = []
        kinds = filter_kinds or ["fact", "preference", "tool_outcome", "scratchpad"]

        for kind in kinds:
            items = [it for it in self.state.items if it.kind == kind]
            if items:
                header = kind.replace("_", " ").upper()
                output.append(f"--- {header} ---")
                for it in items:
                    output.append(f"[{it.timestamp}] {it.content}")

        return "\n".join(output)

    def record_item(self, content: str, kind: str):
        """
        Records a single item in memory and syncs durable items to disk.

        Args:
            content (str): The information to record.
            kind (str): The category of the item (e.g., 'fact', 'tool_outcome').
        """
        item = MemoryItem(kind=kind, content=content)
        self.state.items.append(item)
        self.state.last_updated = datetime.now().isoformat()

        # 1. Save standard session snapshot to artifacts
        self.artifact_store.save("memory_state", self.state.model_dump())

        # 2. If it's a DURABLE KIND (fact or preference), sync to the /state/ folder
        if kind in ["fact", "preference"]:
            durable_items = [
                it.model_dump()
                for it in self.state.items
                if it.kind in ["fact", "preference"]
            ]
            self.state_store.sync_file("durable_state.json", durable_items)
            # Also save a timestamped version for history
            self.state_store.save(f"durable_{kind}", item.model_dump())

    def record_outcome(self, outcome_summary: str):
        """
        Convenience method to record a tool execution outcome.

        Args:
            outcome_summary (str): The summary of what happened.
        """
        self.record_item(outcome_summary, "tool_outcome")
