"""Agent memory management — stores and retrieves reasoning patterns."""


class AgentMemory:
    """Vector + structured memory store for prediction agents"""

    def __init__(self, agent_id: str, db_path: str = "data/memory"):
        self.agent_id = agent_id
        self.db_path = db_path
        self._memories: list[dict] = []

    def add(self, prediction_id: str, outcome: str, reasoning: dict, quality_score: float):
        """Add a settled prediction to memory"""
        self._memories.append({
            "prediction_id": prediction_id,
            "outcome": outcome,
            "reasoning": reasoning,
            "quality_score": quality_score,
            "added_at": __import__("time").time(),
        })

    def query(self, domain: str, topic_keywords: list[str], limit: int = 5) -> list[dict]:
        """Retrieve relevant memories for a new prediction"""
        # In production: vector similarity search
        relevant = [m for m in self._memories if m.get("quality_score", 0) > 0.6]
        return sorted(relevant, key=lambda x: x["quality_score"], reverse=True)[:limit]

    def prune(self, min_quality: float = 0.3):
        """Remove low-quality memories"""
        self._memories = [m for m in self._memories if m.get("quality_score", 0) >= min_quality]
