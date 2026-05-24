"""Prediction scheduler — monitors topics and triggers prediction cycles."""

import time
from src.agents.reasoning import ReasoningEngine, Topic


class PredictionScheduler:
    def __init__(self, engine: ReasoningEngine):
        self.engine = engine

    def run_cycle(self):
        """Run one prediction cycle for all active topics"""
        print("[Scheduler] Running prediction cycle...")

    def predict_single(self, topic_id: str):
        """Predict on a single topic"""
        print(f"[Scheduler] Predicting topic: {topic_id}")
