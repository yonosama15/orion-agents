"""
Structured reasoning engine for AI prediction agents.
Implements long-chain reasoning with evidence verification and confidence calibration.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Conclusion(Enum):
    YES = "yes"
    NO = "no"
    UNDECIDED = "undecided"


class Confidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Evidence:
    """A single piece of evidence supporting or opposing a prediction"""
    claim: str
    source_type: str  # "data", "event", "expert", "historical"
    verifiable: bool
    strength: float  # 0.0 - 1.0
    direction: str  # "supports", "opposes", "neutral"


@dataclass
class Prediction:
    """Structured prediction output from reasoning engine"""
    topic_id: str
    conclusion: Conclusion
    probability: float  # 0-100
    core_evidence: list[Evidence]
    counter_view: str
    invalidation_conditions: list[str]
    confidence: Confidence
    reasoning_chain: list[str]
    timestamp: float = field(default_factory=time.time)
    agent_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "conclusion": self.conclusion.value,
            "probability": self.probability,
            "core_evidence": [
                {"claim": e.claim, "source_type": e.source_type,
                 "verifiable": e.verifiable, "strength": e.strength,
                 "direction": e.direction}
                for e in self.core_evidence
            ],
            "counter_view": self.counter_view,
            "invalidation_conditions": self.invalidation_conditions,
            "confidence": self.confidence.value,
            "reasoning_chain": self.reasoning_chain,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
        }


@dataclass
class Topic:
    """A prediction topic/question"""
    id: str
    question: str
    domain: str
    deadline: float
    context: str = ""
    metadata: dict = field(default_factory=dict)


class ReasoningEngine:
    """
    Multi-step reasoning engine that produces structured predictions.
    
    Pipeline:
    1. Evidence Collection — gather relevant data points
    2. Multi-perspective Analysis — analyze from different angles
    3. Counter-argument Generation — steel-man the opposing view
    4. Confidence Calibration — assess evidence quality and completeness
    5. Invalidation Conditions — define what would change the conclusion
    6. Synthesis — produce final structured prediction
    """

    def __init__(self, model: str = "mimo-v2.5", api_key: str = "", api_base: str = ""):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base or "https://api.platform.xiaomimimo.com/v1"
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        return """You are a prediction agent focused on {domain}.
Your task is to make Yes / No / Undecided predictions on topics and output a structured analysis.

Topic: {question}
Context: {context}

Please always use the following structure:
1) Conclusion: Yes / No / Undecided
2) Probability: 0-100%
3) Core evidence: at least 3 points (with source type or verifiable clues)
4) Counter-view: at least 1 point
5) Invalidation conditions: what new facts would overturn the current conclusion
6) Confidence: Low / Medium / High
7) Reasoning chain: step-by-step logic that led to this conclusion

Rules:
- Do not fabricate sources.
- If the evidence is conflicting or insufficient, prefer Undecided.
- Prioritize recent information that can be cross-verified.
- Consider base rates and historical precedents.
- Acknowledge uncertainty explicitly.

Output as JSON."""

    def predict(self, topic: Topic, agent_memory: list[dict] = None) -> Prediction:
        """
        Run full reasoning pipeline on a topic.
        
        Args:
            topic: The prediction topic
            agent_memory: Previous relevant predictions/outcomes for context
            
        Returns:
            Structured Prediction object
        """
        # Build prompt with memory context
        memory_context = ""
        if agent_memory:
            memory_context = "\n\nRelevant past predictions:\n"
            for mem in agent_memory[-5:]:  # Last 5 relevant memories
                memory_context += f"- {mem.get('summary', '')}\n"

        prompt = self._prompt_template.format(
            domain=topic.domain,
            question=topic.question,
            context=topic.context + memory_context,
        )

        # Call LLM
        response = self._call_llm(prompt)

        # Parse response into structured prediction
        prediction = self._parse_response(response, topic)
        return prediction

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API (MiMo V2.5 or compatible)"""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise prediction analyst. Output structured JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        resp = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _parse_response(self, response: str, topic: Topic) -> Prediction:
        """Parse LLM response into structured Prediction"""
        try:
            # Try JSON parse first
            data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract from text
            data = self._extract_from_text(response)

        # Map conclusion
        conclusion_str = str(data.get("conclusion", "undecided")).lower()
        if "yes" in conclusion_str:
            conclusion = Conclusion.YES
        elif "no" in conclusion_str:
            conclusion = Conclusion.NO
        else:
            conclusion = Conclusion.UNDECIDED

        # Map confidence
        confidence_str = str(data.get("confidence", "medium")).lower()
        if "high" in confidence_str:
            confidence = Confidence.HIGH
        elif "low" in confidence_str:
            confidence = Confidence.LOW
        else:
            confidence = Confidence.MEDIUM

        # Parse evidence
        evidence_list = []
        for e in data.get("core_evidence", data.get("evidence", [])):
            if isinstance(e, str):
                evidence_list.append(Evidence(
                    claim=e, source_type="unknown",
                    verifiable=False, strength=0.5, direction="supports"
                ))
            elif isinstance(e, dict):
                evidence_list.append(Evidence(
                    claim=e.get("claim", e.get("point", "")),
                    source_type=e.get("source_type", "unknown"),
                    verifiable=e.get("verifiable", False),
                    strength=e.get("strength", 0.5),
                    direction=e.get("direction", "supports"),
                ))

        # Parse invalidation conditions
        invalidation = data.get("invalidation_conditions", [])
        if isinstance(invalidation, str):
            invalidation = [invalidation]

        return Prediction(
            topic_id=topic.id,
            conclusion=conclusion,
            probability=float(data.get("probability", 50)),
            core_evidence=evidence_list,
            counter_view=str(data.get("counter_view", "")),
            invalidation_conditions=invalidation,
            confidence=confidence,
            reasoning_chain=data.get("reasoning_chain", []),
        )

    def _extract_from_text(self, text: str) -> dict:
        """Fallback parser for non-JSON responses"""
        result = {
            "conclusion": "undecided",
            "probability": 50,
            "core_evidence": [],
            "counter_view": "",
            "invalidation_conditions": [],
            "confidence": "medium",
            "reasoning_chain": [],
        }

        lines = text.strip().split("\n")
        for line in lines:
            line_lower = line.lower().strip()
            if "conclusion:" in line_lower:
                if "yes" in line_lower:
                    result["conclusion"] = "yes"
                elif "no" in line_lower:
                    result["conclusion"] = "no"
            elif "probability:" in line_lower:
                import re
                nums = re.findall(r"(\d+)", line)
                if nums:
                    result["probability"] = int(nums[0])
            elif "confidence:" in line_lower:
                if "high" in line_lower:
                    result["confidence"] = "high"
                elif "low" in line_lower:
                    result["confidence"] = "low"

        return result
