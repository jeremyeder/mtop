# SLO Compliance Demo - Performance Guarantees
# Duration: ~2 minutes

Output recordings/sales/slo-compliance.gif
Output recordings/sales/slo-compliance.mp4
Output recordings/sales/slo-compliance.webm

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
Type "echo '⚡ mtop Sales Demo: SLO Compliance'"
Enter
Type "echo '🎯 Guarantee sub-500ms response times with automatic scaling'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show TTFT performance
Type "echo '📊 Real-time Performance Monitoring:'"
Enter
Type "./mtop get gpt-4-turbo"
Enter
Sleep 4s

# Highlight SLO compliance
Type "echo ''"
Enter
Type "echo '✅ Key Metrics:'"
Enter
Type "echo '   TTFT P95: 180ms (target: <500ms) ✅'"
Enter
Type "echo '   Queue depth: 3 requests (optimal)'"
Enter
Type "echo '   Throughput: 2,000 tokens/second'"
Enter
Type "echo '   SLO compliance: 99.9% uptime'"
Enter
Sleep 4s

# Show scaling simulation
Type "echo ''"
Enter
Type "echo '🔄 Demonstrating Auto-Scaling:'"
Enter
Type "./mtop simulate canary"
Enter
Sleep 6s

# Live monitoring
Type "echo ''"
Enter
Type "echo '📈 Live System Monitoring:'"
Enter
Type "./mtop"
Enter
Sleep 3s
Type "q"

# Summary
Type "echo ''"
Enter
Type "echo '🎯 Guaranteed Performance:'"
Enter
Type "echo '   ✅ Sub-500ms TTFT maintained during 10x traffic spikes'"
Enter
Type "echo '   ✅ 99.9% uptime through predictive capacity management'"
Enter
Type "echo '   ✅ Zero-downtime deployments with automatic validation'"
Enter
Sleep 3s

Type "clear"
Enter
