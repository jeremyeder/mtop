# GitHub Branch Protection Setup

## Why This is Critical
Without branch protection, the CI checks are **advisory only** - PRs can merge even if linting/tests fail!

## Option 1: Make Repository Public (Recommended)
```bash
gh repo edit --visibility public
```
Then run:
```bash
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

## Option 2: Manual Setup (Private Repo)

### Step 1: Go to Repository Settings
1. Navigate to your repository on GitHub
2. Click "Settings" tab
3. Click "Branches" in left sidebar

### Step 2: Add Branch Protection Rule
1. Click "Add rule" 
2. Branch name pattern: `main`

### Step 3: Configure Protection Settings
```
☑ Require a pull request before merging
  ☑ Require approvals: 1
  ☑ Dismiss stale PR approvals when new commits are pushed

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  ☑ Status checks that are required:
      - test (this must match the job name in CI)

☑ Include administrators

☐ Allow force pushes (leave unchecked)
☐ Allow deletions (leave unchecked)
```

### Step 4: Save Changes
Click "Create" to enable protection.

## Verification
1. Create a test branch with broken code
2. Open PR - should show failing CI
3. Verify merge button is disabled until CI passes

## Result
After setup:
- ❌ Cannot merge PRs with failing CI
- ❌ Cannot push directly to main
- ✅ Pre-commit hooks catch issues locally  
- ✅ CI provides fast feedback on PRs