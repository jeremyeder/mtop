# 🤝 Collaboration Workflow

> **How Jeremy and Claude work together through GitHub issues and project boards**

---

## 🎯 Overview

This document explains our manual collaboration workflow for the GPU Heartbeat & SLO Convergence demo system. Since Claude cannot receive real-time notifications, we use a simple, effective manual process through GitHub.

## 📋 Project Board Workflow

### GitHub Project Board
- **URL**: https://github.com/users/jeremyeder/projects/3
- **Columns**: Backlog → TODO → In Progress → Done
- **45 Total Issues**: 4 Epics + 41 implementation tasks

### How It Works

1. **Jeremy moves tickets** from Backlog → TODO when ready to start
2. **Jeremy tells Claude** "Check the project board" or "Start on #35"
3. **Claude checks** TODO column and responds with plan
4. **Claude works** on issues, providing progress updates
5. **Jeremy moves tickets** to Done when satisfied

## 💬 Issue Comment Workflow

### Starting Work
```
Jeremy: "Start working on #35"
Claude: Comments "Starting work on this issue" + implementation plan
Claude: Regular progress updates in issue comments
Jeremy: Reviews work and provides feedback
```

### Getting Updates
```
Jeremy: "Status update on #15"
Claude: Provides current progress, next steps, any blockers
```

### Asking Questions
```
Jeremy: "Check comments on #27 - I have questions"
Claude: Reviews all comments and responds accordingly
```

## 🔄 Typical Session Flow

### Session Start
1. **Jeremy**: "Check the project board"
2. **Claude**: Reviews TODO column, reports what's ready
3. **Jeremy**: "Start with #35, then #15"
4. **Claude**: Begins work on #35, comments progress

### During Work
1. **Claude**: Regular progress updates in issue comments
2. **Claude**: Asks questions if blocked or needs clarification
3. **Jeremy**: Provides feedback and direction as needed

### Session End
1. **Claude**: Commits work with detailed commit messages
2. **Claude**: Updates issue comments with current status
3. **Jeremy**: Reviews work, moves completed tickets to Done

## ⚡ Quick Commands

### For Jeremy to Use
- `"Check the project board"` - Review all current tickets
- `"Start on #N"` - Begin work on specific issue
- `"Check issue #N"` - Review specific issue and comments
- `"Status update"` - Get progress report on current work
- `"Check TODO"` - See what's ready to start

### For Claude Response Pattern
- **Always comment** "Starting work on this issue" when beginning
- **Provide implementation plan** in first comment
- **Regular progress updates** as work progresses
- **Ask for clarification** when blocked
- **Summarize completion** when done

## 🎬 VHS Demo Workflow

Each Epic has a completion milestone - a 60-second VHS demo:

1. **Complete Epic sub-tasks** (e.g., #15-18 for Epic #14)
2. **Jeremy**: "Create VHS demo for Epic #14"
3. **Claude**: Records demo, generates multiple formats
4. **Epic marked complete** with demo as proof

## 📚 Documentation Standards

### Book-Quality Requirements
- **Complete reproducibility** - anyone can follow instructions
- **Capture all artifacts** - configs, YAML, generated files
- **Professional presentation** - suitable for "Life with llm-d" book
- **Academic rigor** - performance analysis and benchmarking

### Documentation Workflow
- **#35**: Documentation structure (can start immediately)
- **#36**: Architecture documentation (after core infrastructure)
- **#37**: Artifact capture (ongoing throughout development)
- **#38**: Reproduction guides (after system completion)

## 🎯 Current Priorities

### Ready to Start (No Dependencies)
1. **#35** - Create book-quality documentation structure
2. **#15** - Enhanced configuration system (foundation for everything)
3. **#8** - Fix argument parsing logic (current broken functionality)

### Critical Path
```
#15 (config) → #16 (tokens) + #17 (heartbeat) → #18 (DRA) → #40 (VHS demo)
              ↓
#26 (workload) → #27 (SLO algorithm) → #28 (queue) → #41 (VHS demo)
                 ↓
#29 (animation) → #30 (dashboard) → #31 (executive) → #42 (VHS demo)
                  ↓
#32 (spike) → #33 (deployment) → #34 (contention) → #43 (final VHS demo)
```

## 🚨 Important Notes

### Claude Limitations
- **No real-time notifications** - cannot monitor GitHub automatically
- **Session-based only** - must be prompted to check for changes
- **Manual workflow required** - Jeremy must direct all activities

### What Works Well
- **Clear communication** through issue comments
- **Structured project board** with logical priority order
- **Frequent commits** with detailed messages
- **Progress tracking** through issue updates

## 🏆 Success Metrics

### For Each Epic
- ✅ All sub-tasks completed
- ✅ 60-second VHS demo recorded
- ✅ Documentation updated
- ✅ Artifacts captured

### Final Success
- ✅ **Demonstrate llm-d autonomously converges on cost/performance SLOs**
- ✅ Complete system ready for "Life with llm-d" book
- ✅ Professional-quality demos and documentation
- ✅ Fully reproducible system

---

## 🚀 Ready to Start!

**Next Actions**:
1. Jeremy moves desired tickets to TODO
2. Jeremy tells Claude which to start with
3. Claude begins work with progress updates
4. Collaborate through issue comments
5. Build amazing GPU heartbeat SLO convergence system!

*This workflow ensures efficient collaboration while maintaining full transparency and professional quality for book inclusion.*