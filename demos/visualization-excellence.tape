# VHS Demo: Visualization Excellence
# GPU Infrastructure Monitoring with Real-time Analytics
# Duration: ~60 seconds of pure visualization excellence

Output demos/visualization-excellence.gif
Output demos/visualization-excellence.mp4

Set Shell python3
Set Theme "Monokai Pro"
Set FontSize 16
Set Width 1400
Set Height 800
Set Padding 20
Set Framerate 30

# Demo starts with a clean slate
Type@500ms "clear"
Enter
Sleep 1s

# ====================
# PHASE 1: Heartbeat Animation (20 seconds)
# ====================
Type@300ms "# 🔥 PHASE 1: GPU Heartbeat Animation"
Enter
Sleep 1s

Type@200ms "# Real-time GPU capacity visualization with technology-specific characteristics"
Enter
Sleep 500ms

Type@200ms "python3 -c \""
Type@100ms "from mtop.heartbeat_visualizer import create_demo_scenario"
Enter
Type@100ms "animator, heartbeat = create_demo_scenario()"
Enter
Type@100ms "print('✨ Starting GPU heartbeat animation with DRA technology...')"
Enter
Type@100ms "import threading"
Enter
Type@100ms "sim_thread = threading.Thread(target=heartbeat.simulate_workload, args=(75.0, 15.0), daemon=True)"
Enter
Type@100ms "sim_thread.start()"
Enter
Type@100ms "animator.run_live_animation(heartbeat, duration_seconds=12.0, refresh_rate=8.0)"
Enter
Type@50ms "\""
Enter

# Let the heartbeat animation run for dramatic effect
Sleep 13s

# ====================
# PHASE 2: SLO Dashboard (20 seconds)
# ====================
Type@500ms "clear"
Enter
Sleep 500ms

Type@300ms "# 📊 PHASE 2: SLO Compliance Dashboard"
Enter
Sleep 1s

Type@200ms "# Twin gauges showing TTFT and cost metrics with convergence tracking"
Enter
Sleep 500ms

Type@200ms "python3 -c \""
Type@100ms "from mtop.slo_dashboard import SLODashboard"
Enter
Type@100ms "from mtop.slo_convergence import ConvergenceMetrics"
Enter
Type@100ms "from config_loader import SLOConfig"
Enter
Type@100ms "import time"
Enter
Type@100ms "print('📈 Launching SLO dashboard with convergence metrics...')"
Enter
Type@100ms "dashboard = SLODashboard(None)"
Enter
Type@100ms "for i in range(15):"
Enter
Type@100ms "    metrics = ConvergenceMetrics(current_ttft_p95=200+i*5, current_cost_per_million=0.15+i*0.01)"
Enter
Type@100ms "    dashboard.update_metrics(metrics, gpu_count=4)"
Enter
Type@100ms "    print(f'📊 SLO Update {i+1}/15: TTFT={200+i*5}ms, Cost=${0.15+i*0.01:.2f}/M')"
Enter
Type@100ms "    time.sleep(0.8)"
Enter
Type@50ms "\""
Enter

# Let the SLO dashboard run and show convergence
Sleep 13s

# ====================
# PHASE 3: Executive Summary (20 seconds)
# ====================
Type@500ms "clear"
Enter
Sleep 500ms

Type@300ms "# 🏢 PHASE 3: Executive Dashboard"
Enter
Sleep 1s

Type@200ms "# Business value metrics: cost savings, ROI, SLO compliance"
Enter
Sleep 500ms

Type@200ms "python3 -c \""
Type@100ms "from mtop.executive_view import create_demo_executive_view"
Enter
Type@100ms "print('💰 Launching executive dashboard with business metrics...')"
Enter
Type@100ms "dashboard, heartbeat = create_demo_executive_view()"
Enter
Type@100ms "import threading"
Enter
Type@100ms "sim_thread = threading.Thread(target=heartbeat.simulate_workload, args=(65.0, 12.0), daemon=True)"
Enter
Type@100ms "sim_thread.start()"
Enter
Type@100ms "dashboard.run_live_dashboard(heartbeat, duration_seconds=10.0, refresh_rate=3.0)"
Enter
Type@50ms "\""
Enter

# Let the executive dashboard show business value
Sleep 12s

# ====================
# FINALE: Real-time Integration
# ====================
Type@500ms "clear"
Enter
Sleep 500ms

Type@300ms "# ⚡ FINALE: Real-time Integration"
Enter
Sleep 1s

Type@200ms "# All visualization components with synchronized real-time updates"
Enter
Sleep 500ms

Type@200ms "python3 -c \""
Type@100ms "from mtop.real_time_updates import create_demo_real_time_system"
Enter
Type@100ms "print('🚀 Launching integrated real-time visualization system...')"
Enter
Type@100ms "viz_manager, heartbeat = create_demo_real_time_system()"
Enter
Type@100ms "import threading"
Enter
Type@100ms "sim_thread = threading.Thread(target=heartbeat.simulate_workload, args=(80.0, 8.0), daemon=True)"
Enter
Type@100ms "sim_thread.start()"
Enter
Type@100ms "viz_manager.start_real_time_updates(heartbeat)"
Enter
Type@100ms "import time; time.sleep(6.0)"
Enter
Type@100ms "viz_manager.stop_real_time_updates()"
Enter
Type@100ms "print('✅ Visualization excellence demo complete!')"
Enter
Type@50ms "\""
Enter

# Final dramatic pause showing the completed system
Sleep 8s

# Demo conclusion
Type@500ms "clear"
Enter
Sleep 500ms

Type@300ms "# 🎯 VISUALIZATION EXCELLENCE ACHIEVED"
Enter
Sleep 1s

Type@200ms "echo ''"
Enter
Type@200ms "echo '🔥 GPU Heartbeat Animation: Technology-specific pulsing with DRA (cyan, 2.0Hz)'"
Enter
Type@200ms "echo '📊 SLO Dashboard: Twin gauges with TTFT and cost convergence tracking'"
Enter
Type@200ms "echo '🏢 Executive View: Business metrics with ROI and cost optimization'"
Enter  
Type@200ms "echo '⚡ Real-time Updates: Synchronized streaming across all components'"
Enter
Type@200ms "echo ''"
Enter
Type@200ms "echo '💡 llm-d: Autonomous GPU infrastructure optimization'"
Enter
Type@200ms "echo '🚀 Ready for production deployment!'"
Enter

Sleep 3s