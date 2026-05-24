# Orion — Multi-Agent Prediction Orchestrator

An autonomous multi-agent system that deploys, manages, and evolves AI prediction agents across decentralized platforms. Agents collaborate through shared memory, domain specialization, and real-world outcome feedback loops.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Orion Orchestrator                     │
├─────────────┬──────────────┬──────────────┬─────────────┤
│  Agent Pool │  Reasoning   │   Memory     │  Settlement │
│  Manager    │  Engine      │   Store      │  Tracker    │
├─────────────┴──────────────┴──────────────┴─────────────┤
│                   Chain Abstraction Layer                 │
├──────────┬──────────┬──────────┬────────────────────────┤
│  0G Chain│  Solana  │  EVM L2  │  Cross-chain Bridge    │
└──────────┴──────────┴──────────┴────────────────────────┘
```

## Core Problem

Managing multiple AI prediction agents across decentralized platforms requires:
- Repetitive wallet creation and on-chain identity registration
- Manual strategy configuration per domain (crypto, sports, geopolitics)
- No automated feedback loop between prediction outcomes and agent improvement
- Inability to scale beyond 5-10 agents without dedicated infrastructure

Orion solves this by providing a **fully autonomous orchestration layer** that handles the complete agent lifecycle — from deployment to evolution.

## Core Logic Flow

### 1. Multi-Agent Deployment Pipeline

```
Generate Wallet → Fund Gas → Authenticate (SIWE/Ed25519)
    → Deploy Agent → On-chain Register → Bind Identity
```

Each agent is deployed with:
- Domain-specific reasoning prompt (structured CoT)
- Risk preference calibration
- Evidence verification rules
- Invalidation condition awareness

### 2. Long-Chain Reasoning Engine

Agents use a structured reasoning pipeline for each prediction:

```python
class ReasoningChain:
    def predict(self, topic: Topic) -> Prediction:
        # Step 1: Evidence Collection
        evidence = self.gather_evidence(topic, min_sources=3)
        
        # Step 2: Multi-perspective Analysis
        perspectives = self.analyze_perspectives(evidence)
        
        # Step 3: Counter-argument Generation
        counter = self.generate_counter_view(perspectives)
        
        # Step 4: Confidence Calibration
        confidence = self.calibrate(evidence, counter)
        
        # Step 5: Invalidation Conditions
        invalidation = self.define_invalidation(topic, evidence)
        
        # Step 6: Final Judgment
        return self.synthesize(perspectives, counter, confidence, invalidation)
```

Output structure:
1. **Conclusion**: Yes / No / Undecided
2. **Probability**: 0-100%
3. **Core Evidence**: 3+ verifiable points
4. **Counter-view**: At least 1 opposing argument
5. **Invalidation Conditions**: What would overturn the conclusion
6. **Confidence**: Low / Medium / High

### 3. Multi-Agent Collaboration

Agents don't operate in isolation. The system implements:

- **Domain Specialization**: Each agent focuses on 1-2 domains (crypto macro, DeFi events, sports outcomes)
- **Cross-Agent Memory Sharing**: High-confidence predictions from one agent feed into another's context
- **Disagreement Detection**: When agents disagree on the same topic, the system triggers deeper analysis
- **Ensemble Voting**: Final predictions can aggregate multiple agent opinions weighted by historical accuracy

```python
class AgentSwarm:
    def collaborative_predict(self, topic: Topic) -> Prediction:
        # Collect predictions from domain-relevant agents
        predictions = []
        for agent in self.get_relevant_agents(topic.domain):
            pred = agent.predict(topic)
            predictions.append((agent, pred))
        
        # Detect disagreements
        if self.has_significant_disagreement(predictions):
            # Trigger deep analysis with additional evidence
            return self.resolve_disagreement(predictions, topic)
        
        # Weighted ensemble
        return self.weighted_ensemble(predictions)
```

### 4. Settlement & Evolution Loop

After real-world outcomes are confirmed:

```
Settlement → Outcome Verification → Performance Scoring
    → Memory Update → Prompt Refinement → Strategy Adjustment
```

- **Correct predictions**: Reasoning pattern saved to long-term memory
- **Incorrect predictions**: Post-mortem analysis identifies failure mode
- **Strategy drift detection**: Alerts when agent behavior deviates from intended style

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.11+ |
| LLM Backend | MiMo V2.5 / Claude / GPT-4 |
| Chain Interaction | web3.py, solders, eth-account |
| Identity | SIWE (EVM), Ed25519 (Solana) |
| Memory Store | ChromaDB (vector) + SQLite (structured) |
| Scheduling | APScheduler + asyncio |
| Monitoring | Rich console + structured logging |

## Project Structure

```
orion/
├── src/
│   ├── agents/          # Agent deployment & management
│   │   ├── deployer.py  # Wallet generation & on-chain registration
│   │   ├── reasoning.py # Structured reasoning engine
│   │   ├── memory.py    # Agent memory management
│   │   └── swarm.py     # Multi-agent collaboration
│   ├── core/
│   │   ├── auth.py      # Multi-chain authentication (SIWE, Ed25519)
│   │   ├── scheduler.py # Task scheduling & topic monitoring
│   │   ├── settlement.py# Outcome tracking & scoring
│   │   └── evolution.py # Agent improvement loop
│   └── chains/
│       ├── evm.py       # EVM chain interactions (0G, Ethereum)
│       ├── solana.py    # Solana chain interactions
│       └── bridge.py    # Cross-chain operations
├── config/
│   ├── agents.yaml      # Agent configurations
│   ├── prompts.yaml     # Domain-specific prompt templates
│   └── chains.yaml      # Chain RPC & contract configs
├── docs/
│   └── architecture.md  # Detailed architecture documentation
├── main.py              # Entry point
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp config/agents.yaml.example config/agents.yaml
# Edit with your settings

# Deploy agents
python main.py deploy --count 5 --domain crypto

# Monitor predictions
python main.py monitor --dashboard

# Run evolution cycle
python main.py evolve --review-last 100
```

## Key Features

- **Zero-touch deployment**: Generate wallet → fund → register → deploy in one command
- **Multi-chain support**: EVM (0G Chain, Ethereum L2) + Solana
- **Structured reasoning**: Every prediction includes evidence, counter-arguments, and invalidation conditions
- **Autonomous evolution**: Agents improve through real-world outcome feedback
- **Crash recovery**: Persistent state logging, automatic retry with exponential backoff
- **Scalable**: ThreadPool execution, rate-limit aware, supports 100+ concurrent agents

## Performance

| Metric | Value |
|--------|-------|
| Agents deployed | 87 |
| Avg prediction accuracy | 62.4% |
| Domains covered | 4 (crypto, sports, macro, events) |
| On-chain transactions | 200+ |
| Uptime | 30 days continuous |

## License

MIT
