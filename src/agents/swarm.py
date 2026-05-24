"""
Multi-agent swarm collaboration module.
Implements ensemble predictions, disagreement resolution, and cross-agent memory sharing.
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from src.agents.reasoning import ReasoningEngine, Prediction, Topic, Confidence


@dataclass
class AgentProfile:
    """Profile of a deployed prediction agent"""
    agent_id: str
    address: str
    domain: str
    style: str
    win_rate: float = 0.0
    total_predictions: int = 0
    streak: int = 0
    memory: list[dict] = field(default_factory=list)


class AgentSwarm:
    """
    Manages a swarm of prediction agents with collaborative capabilities.
    
    Features:
    - Domain-based agent routing
    - Ensemble voting with accuracy-weighted opinions
    - Disagreement detection and resolution
    - Cross-agent memory sharing for related domains
    """

    def __init__(self, agents: list[AgentProfile] = None, engine: ReasoningEngine = None):
        self.agents = agents or []
        self.engine = engine or ReasoningEngine()
        self._prediction_history: list[dict] = []

    @classmethod
    def load_from_config(cls, config_path: str = "config/agents.yaml") -> "AgentSwarm":
        """Load swarm configuration from YAML"""
        # In production, load from config file
        return cls()

    def get_relevant_agents(self, domain: str) -> list[AgentProfile]:
        """Get agents specialized in a given domain"""
        primary = [a for a in self.agents if a.domain == domain]
        # Include high-performing generalists
        generalists = [a for a in self.agents if a.win_rate > 0.65 and a.domain != domain]
        return primary + generalists[:2]

    def collaborative_predict(self, topic: Topic) -> Prediction:
        """
        Generate prediction using multi-agent collaboration.
        
        Flow:
        1. Route topic to domain-relevant agents
        2. Each agent generates independent prediction
        3. Check for significant disagreement
        4. If disagreement: trigger deep analysis
        5. If consensus: return weighted ensemble
        """
        relevant_agents = self.get_relevant_agents(topic.domain)

        if not relevant_agents:
            # Fallback to single-agent prediction
            return self.engine.predict(topic)

        # Collect predictions from each agent
        predictions: list[tuple[AgentProfile, Prediction]] = []
        for agent in relevant_agents:
            pred = self.engine.predict(topic, agent_memory=agent.memory)
            pred.agent_id = agent.agent_id
            predictions.append((agent, pred))

        # Check for disagreement
        if self._has_significant_disagreement(predictions):
            return self._resolve_disagreement(predictions, topic)

        # Weighted ensemble
        return self._weighted_ensemble(predictions)

    def _has_significant_disagreement(self, predictions: list[tuple[AgentProfile, Prediction]]) -> bool:
        """Check if agents significantly disagree"""
        conclusions = [p.conclusion for _, p in predictions]
        unique = set(c.value for c in conclusions)

        # Disagreement if both YES and NO present
        if "yes" in unique and "no" in unique:
            return True

        # Disagreement if probability spread > 40%
        probs = [p.probability for _, p in predictions]
        if probs and (max(probs) - min(probs)) > 40:
            return True

        return False

    def _resolve_disagreement(self, predictions: list[tuple[AgentProfile, Prediction]], topic: Topic) -> Prediction:
        """
        Resolve disagreement through deeper analysis.
        
        Strategy:
        1. Identify the core point of disagreement
        2. Request additional evidence from each side
        3. Weight by historical accuracy in this domain
        4. If still unresolved, output Undecided with high uncertainty
        """
        # Weight by win rate
        weighted_yes = sum(
            agent.win_rate * pred.probability
            for agent, pred in predictions
            if pred.conclusion.value == "yes"
        )
        weighted_no = sum(
            agent.win_rate * (100 - pred.probability)
            for agent, pred in predictions
            if pred.conclusion.value == "no"
        )

        total_weight = sum(agent.win_rate for agent, _ in predictions) or 1

        # If still close, mark as undecided
        if abs(weighted_yes - weighted_no) < total_weight * 10:
            # Use the highest-confidence agent's reasoning
            best_agent, best_pred = max(predictions, key=lambda x: x[0].win_rate)
            best_pred.confidence = Confidence.LOW
            best_pred.reasoning_chain.append(
                f"[SWARM] Disagreement detected among {len(predictions)} agents. "
                f"Confidence reduced due to conflicting signals."
            )
            return best_pred

        # Go with weighted majority
        if weighted_yes > weighted_no:
            winner = max(
                [(a, p) for a, p in predictions if p.conclusion.value == "yes"],
                key=lambda x: x[0].win_rate
            )
        else:
            winner = max(
                [(a, p) for a, p in predictions if p.conclusion.value == "no"],
                key=lambda x: x[0].win_rate
            )

        _, result = winner
        result.reasoning_chain.append(
            f"[SWARM] Ensemble of {len(predictions)} agents. "
            f"Weighted consensus: YES={weighted_yes:.0f} vs NO={weighted_no:.0f}"
        )
        return result

    def _weighted_ensemble(self, predictions: list[tuple[AgentProfile, Prediction]]) -> Prediction:
        """Combine predictions using accuracy-weighted voting"""
        if not predictions:
            raise ValueError("No predictions to ensemble")

        # Weight by win rate
        total_weight = sum(max(agent.win_rate, 0.1) for agent, _ in predictions)
        weighted_prob = sum(
            agent.win_rate * pred.probability
            for agent, pred in predictions
        ) / total_weight

        # Use best agent's full prediction as base
        best_agent, best_pred = max(predictions, key=lambda x: x[0].win_rate)
        best_pred.probability = weighted_prob
        best_pred.reasoning_chain.append(
            f"[SWARM] Ensemble of {len(predictions)} agents. "
            f"Weighted probability: {weighted_prob:.1f}%"
        )

        return best_pred

    def share_memory(self, source_agent: AgentProfile, target_agent: AgentProfile, memory_item: dict):
        """Share a memory item from one agent to another"""
        if memory_item not in target_agent.memory:
            target_agent.memory.append(memory_item)

    def print_status(self):
        """Print swarm status"""
        print(f"\n{'='*50}")
        print(f"  Agent Swarm Status")
        print(f"  Total agents: {len(self.agents)}")
        print(f"{'='*50}")
        for agent in self.agents:
            print(f"  [{agent.agent_id}] {agent.domain} | "
                  f"WR: {agent.win_rate:.1%} | "
                  f"Preds: {agent.total_predictions} | "
                  f"Streak: {agent.streak}")

    def run_dashboard(self):
        """Run live monitoring dashboard"""
        # In production: rich live display
        self.print_status()
