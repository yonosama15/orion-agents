"""
Orion — Multi-Agent Prediction Orchestrator
Entry point for deploying, monitoring, and evolving AI prediction agents.
"""

import argparse
import sys
from pathlib import Path

from src.core.auth import MultiChainAuth
from src.agents.deployer import AgentDeployer
from src.agents.swarm import AgentSwarm
from src.agents.reasoning import ReasoningEngine
from src.core.scheduler import PredictionScheduler
from src.core.settlement import SettlementTracker
from src.core.evolution import EvolutionEngine


def cmd_deploy(args):
    """Deploy new prediction agents"""
    print(f"[Orion] Deploying {args.count} agents on domain: {args.domain}")

    deployer = AgentDeployer(
        chain=args.chain,
        domain=args.domain,
        gas_per_agent=args.gas,
    )

    results = deployer.deploy_batch(
        count=args.count,
        referral_code=args.ref,
        parallel=args.parallel,
    )

    success = sum(1 for r in results if r["status"] == "success")
    print(f"\n[Orion] Deployed: {success}/{args.count} agents")
    print(f"[Orion] Results saved to: {deployer.results_file}")


def cmd_monitor(args):
    """Monitor active agents and their predictions"""
    swarm = AgentSwarm.load_from_config()

    if args.dashboard:
        swarm.run_dashboard()
    else:
        swarm.print_status()


def cmd_predict(args):
    """Run prediction cycle for all active agents"""
    engine = ReasoningEngine(model=args.model)
    scheduler = PredictionScheduler(engine=engine)

    if args.topic:
        scheduler.predict_single(args.topic)
    else:
        scheduler.run_cycle()


def cmd_evolve(args):
    """Run evolution cycle — review settlements and improve agents"""
    tracker = SettlementTracker()
    evolution = EvolutionEngine(tracker=tracker)

    print(f"[Orion] Reviewing last {args.review_last} predictions...")
    report = evolution.run_cycle(lookback=args.review_last)

    print(f"\n[Orion] Evolution Report:")
    print(f"  Reviewed: {report['total_reviewed']}")
    print(f"  Correct: {report['correct']} ({report['accuracy']:.1%})")
    print(f"  Memory updates: {report['memory_updates']}")
    print(f"  Prompt adjustments: {report['prompt_adjustments']}")


def main():
    parser = argparse.ArgumentParser(
        description="Orion — Multi-Agent Prediction Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deploy new agents")
    deploy_parser.add_argument("--count", type=int, default=5, help="Number of agents")
    deploy_parser.add_argument("--domain", default="crypto", help="Domain focus")
    deploy_parser.add_argument("--chain", default="0g", help="Target chain (0g, solana)")
    deploy_parser.add_argument("--gas", type=float, default=0.003, help="Gas per agent")
    deploy_parser.add_argument("--ref", default=None, help="Referral code")
    deploy_parser.add_argument("--parallel", type=int, default=3, help="Parallel workers")

    # Monitor
    monitor_parser = subparsers.add_parser("monitor", help="Monitor agents")
    monitor_parser.add_argument("--dashboard", action="store_true", help="Live dashboard")

    # Predict
    predict_parser = subparsers.add_parser("predict", help="Run prediction cycle")
    predict_parser.add_argument("--topic", default=None, help="Specific topic ID")
    predict_parser.add_argument("--model", default="mimo-v2.5", help="LLM model")

    # Evolve
    evolve_parser = subparsers.add_parser("evolve", help="Run evolution cycle")
    evolve_parser.add_argument("--review-last", type=int, default=100, help="Predictions to review")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "deploy": cmd_deploy,
        "monitor": cmd_monitor,
        "predict": cmd_predict,
        "evolve": cmd_evolve,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
