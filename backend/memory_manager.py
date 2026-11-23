from pathlib import Path
from datetime import datetime
from typing import List, Dict, Literal
from backend.config import MEMORY_DIR

MemoryScope = Literal["agents", "rooms", "projects"]

class MemoryManager:
    def __init__(self):
        self.base = MEMORY_DIR

    def _get_path(self, scope: MemoryScope, entity_id: str) -> Path:
        safe_id = "".join(c for c in entity_id if c.isalnum() or c in ("-", "_"))
        path = self.base / scope / f"{safe_id}.md"
        if not path.exists():
            header = f"# {scope.capitalize()} Memory: {safe_id}\n\n"
            path.write_text(header, encoding="utf-8")
        return path

    def list_memories(self) -> List[Dict[str, str]]:
        items = []
        for scope in ["agents", "rooms", "projects"]:
            for file in sorted((self.base / scope).glob("*.md")):
                items.append({
                    "scope": scope,
                    "entity_id": file.stem,
                    "filename": f"{scope}/{file.name}",
                    "updated_at": datetime.utcfromtimestamp(file.stat().st_mtime).isoformat() + "Z"
                })
        return items

    def read_memory(self, scope: MemoryScope, entity_id: str) -> str:
        # Always reads directly from disk so user/evaluator edits apply immediately
        return self._get_path(scope, entity_id).read_text(encoding="utf-8")

    def write_memory(self, scope: MemoryScope, entity_id: str, content: str) -> str:
        path = self._get_path(scope, entity_id)
        path.write_text(content, encoding="utf-8")
        return content

    def append_provenance_entry(
        self,
        scope: MemoryScope,
        entity_id: str,
        fact: str,
        why: str,
        source: str = "Agent Observation"
    ) -> str:
        path = self._get_path(scope, entity_id)
        existing = path.read_text(encoding="utf-8")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = (
            f"\n### [{timestamp}] | Source: {source}\n"
            f"- **Remembered:** {fact}\n"
            f"- **Why:** {why}\n"
        )
        updated = existing.rstrip() + "\n" + entry
        path.write_text(updated, encoding="utf-8")
        return updated

    def build_context_bundle(self, agent_id: str, room_id: str, project_id: str = "meetuniversity") -> str:
        proj_mem = self.read_memory("projects", project_id)
        room_mem = self.read_memory("rooms", room_id)
        agent_mem = self.read_memory("agents", agent_id)
        return (
            f"=== PROJECT & USER PREFERENCES MEMORY ({project_id}) ===\n{proj_mem}\n\n"
            f"=== SHARED ROOM MEMORY ({room_id}) ===\n{room_mem}\n\n"
            f"=== INDIVIDUAL AGENT MEMORY ({agent_id}) ===\n{agent_mem}"
        )
