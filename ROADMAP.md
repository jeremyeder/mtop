# 📍 mtop: Roadmap to SRE-Grade LLM Debugging Toolkit

---

## 🥇 Milestone 1: Foundations & Simulations

### ✅ CRUD and Mock Mode
- Parse and validate mock CRs from `mocks/crs/`
- Enable full `list`, `get`, `delete`, `create` on mock objects
- Environment-controlled toggle: `LLD_MODE=mock|live`

### ✅ Simulate Topologies
- Structured rollout definitions (canary, bluegreen, rolling, etc.)
- `simulate` CLI command to print timeline per model
- `watch` command with step-by-step or autoplay visual playback

### ✅ Rollout Visualization
- Animated TUI using `rich`, stepping through state transitions
- CLI flags for `--topology`, `--autoplay`, `--delay`

### ✅ Snapshots
- Save current mock/live state to disk with timestamp
- Load and diff snapshots for incident replay/debug

### ✅ Packaging & CLI Ergonomics
- Bash completion for commands + topologies
- JSON/YAML output toggle
- Krew compatibility and install manifest
- README and `--help` for all commands

---

## 🥈 Milestone 2: Live Cluster Support

### 🔍 Cluster Awareness
- Detect if CRDs exist (fail with clear guidance if not)
- Load CRs from `kubectl get ... -o json` when `LLD_MODE=live`
- Graceful fallbacks if user lacks RBAC

### 📝 Live Listing & Inspection
- `kubectl ld list --live`: show live CRs
- Show status, age, readiness, errors inline
- Add `--namespace` and `--all-namespaces` flags

### 📜 Logs
- `kubectl ld logs <model>`:
    - Wrap `kubectl logs` with label selector based on CR
    - Include `--tail`, `--previous`, `--since`

### 🧾 Diffing
- `kubectl ld diff <snapshot>`:
    - Compare live CRs with previously saved mock or snapshot
    - Color-coded output (added, removed, changed keys)
    - Support CR+Config objects in diff

---

## 🥉 Milestone 3: SRE Observability Tools

### 🩺 Health Summary
- `kubectl ld health`:
    - Show high-level readiness of all LLM services
    - Detect Pod OOMs, CrashLoops, long Pending states

### 🔎 Deep Describe
- Extended describe from `kubectl describe`
    - Include Events, container states, last probes
    - Highlight failure reasons (red)

### 📊 Metrics Integration
- Support Prometheus labels for LLM CRs
- List scrape targets or sidecars
- Show token throughput / request rate if available

### ⚠️ Alert Diagnostics
- Parse recent Events for warning patterns:
    - FailedMount
    - ImagePullBackOff
    - NodePressure
- Recommend actions (missing PVCs, wrong nodeSelector, etc.)

---

## 🏅 Milestone 4: Traffic Control & Cost Awareness

### 🔄 Traffic Shift (Mock + API Support)
- `kubectl ld traffic shift gpt2 bert-base 20`
    - Update traffic split in CR or Envoy
    - Print new weights and show transition animation

### 💵 Cost Estimation
- Per-model cost based on:
    - Runtime (e.g., Triton, vLLM)
    - GPU usage class
    - Inference volume
- Show $/req or $/hour estimates per rollout

### 🧪 Load Testing
- `kubectl ld bench gpt2`:
    - Send mock or real prompts
    - Track P50/P95 latency
    - Print QPS/tokens/s breakdown

### 🐌 Latency Simulation
- Annotate rollout simulation with artificial delays or slow start
- Animate as part of `watch`

---

## 🏆 Milestone 5: Interactive & DevEx Polish

### 🖥️ Fullscreen TUI
- Powered by `Textual`
- Switch tabs between:
    - Overview
    - Rollouts
    - Logs
    - Snapshots
- Use keyboard nav to step through model deployments

### 🧠 Doctor Command
- `kubectl ld doctor <model>`:
    - Diagnose common misconfigs:
        - Missing image
        - Wrong volume mount
        - Bad runtime
    - Recommend actions inline

### 🔔 Slack/Webhook Integration
- Webhook config in `.ldconfig`
- Notify on:
    - Rollout failure
    - Crash loop
    - Prometheus alert

### 🔍 GitOps Diff Mode
- `kubectl ld diff prod cluster-snap.yaml`:
    - Compare live state to Git-tracked baseline
    - Show YAML side-by-side changes

---

## 🧱 Infrastructure Milestones

- GitHub CI to test all mock + CLI paths
- Docker image for CLI use in pipelines
- Krew PR and docs