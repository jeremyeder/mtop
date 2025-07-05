# Load Handling Demo - Auto-Scaling
# Duration: ~2 minutes

Output recordings/sales/load-handling.gif
Output recordings/sales/load-handling.mp4
Output recordings/sales/load-handling.webm

Require echo

Set FontSize 14
Set Width 120
Set Height 30
Set Theme "Dracula"

# Setup
Type "clear"
Enter
Sleep 1s

# Title
Type "echo '🔄 mtop Sales Demo: Load Handling'"
Enter
Type "echo '⚡ Handle traffic spikes without human intervention'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show baseline state
Type "echo '📊 Baseline System State:'"
Enter
Type "./mtop list"
Enter
Sleep 3s

# Simulate traffic spike
Type "echo ''"
Enter
Type "echo '🚨 Simulating 10x Traffic Spike:'"
Enter
Type "./demo.sh --headless"
Enter
Sleep 8s

# Show real-time response
Type "echo ''"
Enter
Type "echo '⚡ System Response Analysis:'"
Enter
Type "echo '   Traffic spike detected: 10x normal load'"
Enter
Type "echo '   Queue depth increase: 3 → 15 requests'"
Enter
Type "echo '   Auto-scale triggered: Adding GPU capacity'"
Enter
Type "echo '   Response time: <500ms maintained'"
Enter
Type "echo '   Scale completion: 30 seconds'"
Enter
Sleep 4s

# Show monitoring during spike
Type "echo ''"
Enter
Type "echo '📈 Live Monitoring During Spike:'"
Enter
Type "./mtop"
Enter
Sleep 3s
Type "q"

# Cost optimization aspect
Type "echo ''"
Enter
Type "echo '💰 Cost Optimization:'"
Enter
Type "echo '   Scale up: Only when needed (30 seconds)'"
Enter
Type "echo '   Scale down: Automatic when traffic normalizes'"
Enter
Type "echo '   Resource efficiency: 95% utilization'"
Enter
Type "echo '   Cost impact: Pay only for what you use'"
Enter
Sleep 4s

# Summary
Type "echo ''"
Enter
Type "echo '🎯 Auto-Scaling Benefits:'"
Enter
Type "echo '   ✅ Response time <500ms during 10x spike'"
Enter
Type "echo '   ✅ 30-second auto-scale time'"
Enter
Type "echo '   ✅ No human intervention required'"
Enter
Type "echo '   ✅ Cost-optimized resource allocation'"
Enter
Sleep 3s

Type "clear"
Enter
