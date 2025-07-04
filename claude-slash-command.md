# GitHub Project Management Workflow Setup

Comprehensive GitHub project management automation with time tracking, automated reporting, and engineering management visibility.

## Description

This command sets up a complete collaborative development workflow between developers and Claude, including:
- GitHub project board with comprehensive fields
- Time tracking and sprint planning capabilities  
- Automated progress reporting and dashboards
- Issue templates and collaboration documentation
- Epic-based development with milestone tracking

## Aliases
- `/project:setup`
- `/pm:init`
- `/workflow:create`

## Usage

```bash
/project:setup [project_type] [sprint_days]
```

### Parameters
- `project_type` (optional): Type of project setup
  - `sprint` (default): 8-day sprint-based development
  - `epic`: Epic-based long-term development  
  - `research`: Research and investigation project
  - `minimal`: Basic project with essential fields only

- `sprint_days` (optional): Number of sprint days (default: 8)

### Examples

```bash
# Create full sprint-based project (default)
/project:setup

# Create epic-based project for long-term development
/project:setup epic

# Create 5-day sprint project
/project:setup sprint 5

# Create minimal project with basic fields
/project:setup minimal
```

## Implementation

!PROJECT_TYPE="${1:-sprint}"
!SPRINT_DAYS="${2:-8}"

!echo "🚀 Setting up GitHub Project Management Workflow"
!echo "📋 Project Type: $PROJECT_TYPE"
!echo "⏱️ Sprint Duration: $SPRINT_DAYS days"
!echo ""

# Verify GitHub CLI authentication
!if ! gh auth status &>/dev/null; then
!  echo "❌ GitHub CLI not authenticated. Please run: gh auth login"
!  exit 1
!fi

# Get repository information
!REPO_OWNER=$(gh repo view --json owner --jq '.owner.login')
!REPO_NAME=$(gh repo view --json name --jq '.name')
!echo "📦 Repository: $REPO_OWNER/$REPO_NAME"

# Create GitHub Project
!echo "📋 Creating GitHub Project..."
!PROJECT_TITLE="Development Workflow - $(date +%Y-%m-%d)"
!PROJECT_NUMBER=$(gh project create --owner "$REPO_OWNER" --title "$PROJECT_TITLE" --format json | jq -r '.number')
!PROJECT_ID=$(gh project list --owner "$REPO_OWNER" --format json | jq -r ".projects[] | select(.number == $PROJECT_NUMBER) | .id")

!echo "✅ Created Project #$PROJECT_NUMBER (ID: $PROJECT_ID)"

# Add comprehensive project fields
!echo "🏷️ Adding project fields..."

# Version field for roadmap organization
!gh api graphql -f query="
mutation {
  createProjectV2Field(input: {
    projectId: \"$PROJECT_ID\"
    dataType: SINGLE_SELECT
    name: \"Version\"
    singleSelectOptions: [
      {name: \"v1.0\", color: GRAY, description: \"Current sprint/milestone\"},
      {name: \"v2.0\", color: YELLOW, description: \"Next iteration\"},
      {name: \"v3.0\", color: ORANGE, description: \"Future development\"},
      {name: \"Future\", color: PINK, description: \"Long-term ideas\"}
    ]
  }) {
    projectV2Field { id }
  }
}" > /dev/null

# Time tracking fields
!gh api graphql -f query="
mutation {
  createProjectV2Field(input: {
    projectId: \"$PROJECT_ID\"
    dataType: NUMBER
    name: \"Effort Hours\"
  }) {
    projectV2Field { id }
  }
}" > /dev/null

!gh api graphql -f query="
mutation {
  createProjectV2Field(input: {
    projectId: \"$PROJECT_ID\"
    dataType: NUMBER
    name: \"Actual Hours\"
  }) {
    projectV2Field { id }
  }
}" > /dev/null

!gh api graphql -f query="
mutation {
  createProjectV2Field(input: {
    projectId: \"$PROJECT_ID\"
    dataType: NUMBER
    name: \"Story Points\"
  }) {
    projectV2Field { id }
  }
}" > /dev/null

# Work categorization
!gh api graphql -f query="
mutation {
  createProjectV2Field(input: {
    projectId: \"$PROJECT_ID\"
    dataType: SINGLE_SELECT
    name: \"Work Type\"
    singleSelectOptions: [
      {name: \"Code\", color: GRAY, description: \"Development and implementation\"},
      {name: \"Docs\", color: YELLOW, description: \"Documentation and guides\"},
      {name: \"Demo\", color: ORANGE, description: \"Demonstrations and presentations\"},
      {name: \"Research\", color: PINK, description: \"Investigation and analysis\"},
      {name: \"Testing\", color: GREEN, description: \"Testing and validation\"}
    ]
  }) {
    projectV2Field { id }
  }
}" > /dev/null

# Sprint day assignment (only for sprint projects)
!if [ "$PROJECT_TYPE" = "sprint" ]; then
!  DAY_OPTIONS=""
!  for i in $(seq 1 $SPRINT_DAYS); do
!    if [ $i -eq 1 ]; then
!      DAY_OPTIONS="{name: \"Day$i\", color: GRAY, description: \"Sprint day $i\"}"
!    else
!      DAY_OPTIONS="$DAY_OPTIONS, {name: \"Day$i\", color: GRAY, description: \"Sprint day $i\"}"
!    fi
!  done
!  
!  gh api graphql -f query="
!  mutation {
!    createProjectV2Field(input: {
!      projectId: \"$PROJECT_ID\"
!      dataType: SINGLE_SELECT
!      name: \"Day Assigned\"
!      singleSelectOptions: [$DAY_OPTIONS]
!    }) {
!      projectV2Field { id }
!    }
!  }" > /dev/null
!fi

!echo "✅ Added project fields: Version, Effort Hours, Actual Hours, Story Points, Work Type"

# Create comprehensive labels
!echo "🏷️ Creating repository labels..."

# Categories
!gh label create infrastructure --color 0969da --description "Core infrastructure components" --force
!gh label create visualization --color 1f883d --description "Visualization and UI components" --force  
!gh label create demo --color 8250df --description "Demo scenarios and examples" --force
!gh label create documentation --color 0e8a16 --description "Documentation and guides" --force

# Priorities
!gh label create p0-critical --color b60205 --description "Critical priority - immediate action" --force
!gh label create p1-high --color d93f0b --description "High priority" --force
!gh label create p2-medium --color fbca04 --description "Medium priority" --force
!gh label create p3-low --color 0e8a16 --description "Low priority" --force

# Sizes
!gh label create size-xs --color c5def5 --description "Extra small: 1-2 hours" --force
!gh label create size-s --color c5def5 --description "Small: 2-4 hours" --force
!gh label create size-m --color c5def5 --description "Medium: 1 day" --force
!gh label create size-l --color c5def5 --description "Large: 2-3 days" --force
!gh label create size-xl --color c5def5 --description "Extra large: 1 week" --force

# Types
!gh label create feature --color a2eeef --description "New feature or request" --force
!gh label create research --color d4c5f9 --description "Research and investigation" --force

!echo "✅ Created comprehensive label system"

# Create issue templates
!echo "📝 Creating issue templates..."
!mkdir -p .github/ISSUE_TEMPLATE

!cat > .github/ISSUE_TEMPLATE/feature.md << 'EOF'
---
name: Feature Implementation
about: Implement a new feature or capability
title: ''
labels: feature
assignees: ''
---

## Description
<!-- Brief description of the feature to implement -->

## Requirements
<!-- List specific requirements or acceptance criteria -->
- [ ] 
- [ ] 
- [ ] 

## Technical Details
<!-- Implementation approach, key classes/modules, dependencies -->

## Testing
<!-- How will this feature be tested? -->
- [ ] All tests pass
- [ ] Code coverage maintained/improved
- [ ] Documentation updated

## Documentation
<!-- What documentation needs to be created/updated? -->
- [ ] Code comments added
- [ ] README updated if needed
- [ ] API documentation updated

## Related Issues
<!-- Link to epic or related issues -->
Part of #
EOF

!cat > .github/ISSUE_TEMPLATE/bug.md << 'EOF'
---
name: Bug Report
about: Report a bug or issue
title: ''
labels: bug
assignees: ''
---

## Description
<!-- Clear description of the bug -->

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->

## Environment
- Python version:
- OS:
- Config file (if applicable):

## Logs/Error Messages
```
<!-- Paste any relevant logs or error messages -->
```

## Definition of Done
- [ ] Bug is fixed and verified
- [ ] All tests pass
- [ ] No regression introduced
- [ ] Documentation updated if needed

## Possible Solution
<!-- Optional: Any ideas on how to fix -->
EOF

!cat > .github/ISSUE_TEMPLATE/demo.md << 'EOF'
---
name: Demo/Presentation
about: Create a demonstration or presentation
title: ''
labels: demo
assignees: ''
---

## Demo Overview
<!-- Brief description of what this demo shows -->

## Target Audience
<!-- Who is this demo for? (e.g., executives, engineers, customers) -->

## Key Messages
<!-- What are the main points to convey? -->
1. 
2. 
3. 

## Success Criteria
<!-- What should viewers see/learn? -->
- [ ] Key value proposition clearly demonstrated
- [ ] Professional quality presentation
- [ ] Duration appropriate for audience
- [ ] All functionality works as expected

## Technical Requirements
<!-- What setup or preparation is needed? -->

## Documentation
- [ ] Demo script/narrative created
- [ ] Setup instructions documented
- [ ] Recording/artifacts captured
EOF

!cat > .github/ISSUE_TEMPLATE/research.md << 'EOF'
---
name: Research/Investigation
about: Research task or investigation
title: ''
labels: research
assignees: ''
---

## Research Topic
<!-- What needs to be investigated? -->

## Questions to Answer
- [ ] 
- [ ] 
- [ ] 

## Success Criteria
<!-- When is this research complete? -->
- [ ] All research questions answered
- [ ] Findings documented clearly
- [ ] Recommendations provided
- [ ] Next steps identified

## Resources
<!-- Links, papers, documentation to review -->
- 
- 

## Expected Output
<!-- What deliverable will come from this research? -->
- [ ] Technical design document
- [ ] Proof of concept code
- [ ] Recommendation report
- [ ] Presentation/summary

## Timeline
<!-- When do we need results? -->
EOF

!echo "✅ Created issue templates"

# Create GitHub Actions for progress tracking
!echo "🤖 Setting up automated progress tracking..."
!mkdir -p .github/workflows

!cat > .github/workflows/progress-tracker.yml << 'EOF'
name: Daily Progress Report
on:
  schedule:
    - cron: "0 20 * * *"  # 8PM daily
  workflow_dispatch:        # Manual trigger
  issues:
    types: [closed, reopened]
  pull_request:
    types: [closed, merged]

jobs:
  generate-report:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: read
      pull-requests: read

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Generate Progress Report
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        # Create reports directory
        mkdir -p reports
        
        # Get current date
        DATE=$(date +%Y-%m-%d)
        REPORT_FILE="reports/${DATE}.md"
        
        # Generate daily report template
        cat > "${REPORT_FILE}" << 'EOD'
        # Daily Progress Report - $(date +%Y-%m-%d)
        
        ## Project Overview
        Automated progress tracking for collaborative development workflow.
        
        ### Today's Metrics
        - **Issues Closed**: $(gh issue list --state closed --json closedAt --jq '[.[] | select(.closedAt | startswith("'$DATE'"))] | length')
        - **PRs Merged**: $(gh pr list --state merged --json mergedAt --jq '[.[] | select(.mergedAt | startswith("'$DATE'"))] | length')
        - **Active Issues**: $(gh issue list --state open --json number | jq length)
        
        ### Epic Progress
        <!-- Update manually or with additional automation -->
        
        ### Key Achievements
        <!-- Populated from closed issues today -->
        
        ### Next Steps
        <!-- Based on open high-priority issues -->
        
        ---
        *Generated automatically by GitHub Actions*
        EOD
        
        # Replace date placeholder
        sed -i "s/\$(date +%Y-%m-%d)/${DATE}/g" "${REPORT_FILE}"

    - name: Create Dashboard
      run: |
        cat > reports/dashboard.md << 'EOD'
        # 🚀 Project Management Dashboard
        
        > **Collaborative Development Workflow with Automated Tracking**
        
        ## 📊 Project Overview
        
        ### Current Status
        - **Open Issues**: $(gh issue list --state open --json number | jq length)
        - **Closed Issues**: $(gh issue list --state closed --json number | jq length)
        - **Active Milestones**: $(gh api repos/:owner/:repo/milestones --jq '[.[] | select(.state == "open")] | length')
        
        ### Quick Links
        - [Project Board]($(gh repo view --json url --jq '.url')/projects)
        - [Open Issues]($(gh repo view --json url --jq '.url')/issues)
        - [Documentation](./README.md)
        
        ---
        *Last Updated: $(date)*
        EOD

    - name: Commit Reports
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add reports/
        git commit -m "chore: Generate daily progress report

        Automated project tracking and dashboard update.
        
        Generated by GitHub Actions workflow." || echo "No changes to commit"
        git push || echo "Nothing to push"
EOF

!echo "✅ Created automated progress tracking"

# Create collaboration documentation
!echo "📚 Creating collaboration documentation..."

!cat > COLLABORATION.md << 'EOF'
# 🤝 Collaboration Workflow

> **Comprehensive project management workflow for development teams**

## 🎯 Overview

This project uses a structured collaboration workflow with comprehensive tracking and automated reporting.

## 📋 Project Management

### GitHub Project Board
- **Columns**: Backlog → TODO → In Progress → Done
- **Fields**: Story Points, Effort Hours, Work Type, Version
- **Automation**: Progress tracking and reporting

### Issue Organization
- **Labels**: Priority (p0-p3), Size (xs-xl), Category, Type
- **Templates**: Feature, Bug, Demo, Research
- **Milestones**: Sprint/Epic completion markers

## ⏱️ Time Tracking

### Development Metrics
- **Story Points**: Agile estimation (1,2,3,5,8)
- **Effort Hours**: Time estimates and actuals
- **Work Type**: Code/Docs/Demo/Research/Testing
- **Version**: Release/milestone organization

### Reporting
- **Daily Reports**: Automated progress summaries
- **Dashboard**: Live project metrics
- **Velocity Tracking**: Team performance analysis

## 🔄 Workflow Process

### Issue Lifecycle
1. **Create** issue with appropriate template and labels
2. **Estimate** story points and effort hours
3. **Assign** to sprint/milestone and work type
4. **Develop** with progress updates in comments
5. **Review** and validate completion criteria
6. **Close** with actual time and lessons learned

### Quality Gates
- [ ] All tests pass
- [ ] Code coverage maintained/improved  
- [ ] Documentation updated
- [ ] No breaking changes introduced

## 🚀 Getting Started

1. Review project board and current priorities
2. Pick up issues from TODO column
3. Update progress in issue comments
4. Submit PRs with clear descriptions
5. Ensure all quality gates pass

---

## 📊 Success Metrics

- **Velocity**: Story points completed per period
- **Quality**: Test coverage and defect rates  
- **Predictability**: Estimate accuracy trends
- **Collaboration**: Issue activity and engagement

*This workflow enables efficient collaboration with full visibility into development progress and team performance.*
EOF

!echo "✅ Created collaboration documentation"

# Create reports directory and initial dashboard
!mkdir -p reports

!cat > reports/dashboard.md << 'EOF'
# 🚀 Project Management Dashboard

> **Real-time project tracking and team performance metrics**

## 📊 Current Status

### Project Health
- **Setup**: ✅ Complete
- **Automation**: ✅ Active  
- **Team**: ✅ Ready

### Next Steps
1. Create initial issues and epics
2. Set story points and estimates
3. Begin development workflow
4. Monitor progress through dashboard

## 🔗 Quick Links
- [Project Board]($(gh repo view --json url --jq '.url')/projects)
- [Issue Templates](./.github/ISSUE_TEMPLATE/)
- [Collaboration Guide](./COLLABORATION.md)

---
*Dashboard created by claude-slash project:setup command*
*Last updated: $(date)*
EOF

# Final setup steps
!echo ""
!echo "🎉 GitHub Project Management Workflow Setup Complete!"
!echo ""
!echo "📋 What was created:"
!echo "   ✅ GitHub Project with comprehensive fields"
!echo "   ✅ Complete label system (priorities, sizes, categories)"
!echo "   ✅ Issue templates (feature, bug, demo, research)"
!echo "   ✅ Automated progress tracking (GitHub Actions)"
!echo "   ✅ Collaboration documentation and dashboard"
!echo ""
!echo "🔗 Project URL: $(gh repo view --json url --jq '.url')/projects/$PROJECT_NUMBER"
!echo ""
!echo "🚀 Next steps:"
!echo "   1. Visit the project board and review the setup"
!echo "   2. Create initial issues using the templates"
!echo "   3. Set story points and sprint assignments"
!echo "   4. Begin collaborative development!"
!echo ""
!echo "📚 Documentation:"
!echo "   - Collaboration guide: ./COLLABORATION.md"
!echo "   - Project dashboard: ./reports/dashboard.md"
!echo "   - Issue templates: ./.github/ISSUE_TEMPLATE/"

# Commit all the setup files
!git add .
!git commit -m "feat: Setup comprehensive project management workflow

Created by claude-slash project:setup command

- GitHub project with time tracking fields
- Comprehensive label system  
- Issue templates for all work types
- Automated progress reporting
- Collaboration documentation

Project URL: $(gh repo view --json url --jq '.url')/projects/$PROJECT_NUMBER

Ready for collaborative development with full visibility!"

!echo ""
!echo "✅ All files committed to repository"
!echo "🎯 Workflow setup complete - ready for collaborative development!"

## Features

### 🎯 **Comprehensive Project Setup**
- GitHub project board with custom fields for time tracking
- Complete label system (priorities, sizes, categories, types)
- Issue templates for different work types
- Automated milestone and epic organization

### ⏱️ **Time Tracking & Analytics**
- Story points for agile estimation
- Effort hours tracking (estimated vs actual)
- Work type categorization (Code/Docs/Demo/Research/Testing)
- Sprint day assignments for detailed planning

### 🤖 **Automated Reporting**
- Daily progress reports generated at 8PM
- Project dashboard with real-time metrics
- GitHub Actions integration for automated updates
- Engineering management visibility

### 📚 **Documentation Framework**
- Collaboration guide with workflow processes
- Quality gates and definition of done
- Success metrics and team performance tracking
- Project dashboard with quick links

### 🏗️ **Quality Assurance**
- Test coverage requirements (must pass for merge)
- Documentation exit criteria for all epics
- Manual review process for failing tests
- Emphasis on making tests pass vs bypassing

## Exit Criteria

All epics must meet these criteria before completion:

### Code Quality
- [ ] All tests pass (100% requirement)
- [ ] Test coverage maintained or improved
- [ ] No breaking changes introduced
- [ ] Code review completed

### Documentation  
- [ ] Code comments added for complex logic
- [ ] README updated if functionality changes
- [ ] API documentation current
- [ ] Collaboration guides updated

### Testing Strategy
- Tests must pass before merge (no exceptions)
- Manual review required if tests fail
- Strong emphasis on fixing tests vs bypassing
- Continuous integration validates all changes

## Benefits

- **Complete Visibility**: Full engineering management dashboard
- **Automated Tracking**: No manual reporting overhead  
- **Quality Focus**: Built-in quality gates and test requirements
- **Collaboration Ready**: Structured workflow for team development
- **Scalable**: Works for projects of any size
- **Reusable**: Template-based setup for multiple projects