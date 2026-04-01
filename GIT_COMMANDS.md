# Git Commands Reference

A quick reference for the most commonly used Git commands.

---

## Setup

```bash
# Set your identity (one-time)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Initialize a new repo
git init

# Clone an existing repo
git clone https://github.com/username/repo.git

# Clone into a specific folder
git clone https://github.com/username/repo.git my-folder
```

---

## Daily Workflow

```bash
# Check what's changed
git status

# See the actual diff (unstaged changes)
git diff

# See staged diff (what will be committed)
git diff --staged

# Stage a specific file
git add filename.py

# Stage all changes
git add .

# Commit with a message
git commit -m "Your commit message"

# Stage and commit tracked files in one step
git commit -am "Your commit message"
```

---

## Branches

```bash
# List all local branches
git branch

# List all branches including remote
git branch -a

# Create a new branch
git branch feature/my-feature

# Switch to a branch
git checkout feature/my-feature

# Create and switch in one step
git checkout -b feature/my-feature

# Rename current branch
git branch -m new-name

# Delete a branch (safe — only if merged)
git branch -d feature/my-feature

# Force delete a branch
git branch -D feature/my-feature
```

---

## Remote

```bash
# Check configured remotes
git remote -v

# Add a remote
git remote add origin https://github.com/username/repo.git

# Push to remote (first time — sets upstream)
git push -u origin main

# Push after upstream is set
git push

# Push a specific branch
git push origin feature/my-feature

# Pull latest changes
git pull

# Fetch without merging
git fetch origin
```

---

## History

```bash
# View commit history
git log

# Compact one-line log
git log --oneline

# Log with graph (branches visualized)
git log --oneline --graph --all

# Show changes in a specific commit
git show abc1234

# Who changed what line (blame)
git blame filename.py
```

---

## Undoing Things

```bash
# Unstage a file (keep changes)
git restore --staged filename.py

# Discard unstaged changes to a file (IRREVERSIBLE)
git restore filename.py

# Undo last commit but keep changes staged
git reset --soft HEAD~1

# Undo last commit and unstage changes (changes still in working dir)
git reset HEAD~1

# Undo last commit and discard all changes (IRREVERSIBLE)
git reset --hard HEAD~1

# Create a new commit that reverses a previous commit (safe for shared branches)
git revert abc1234
```

---

## Merging & Rebasing

```bash
# Merge a branch into current branch
git merge feature/my-feature

# Rebase current branch onto main
git rebase main

# Abort a rebase in progress
git rebase --abort

# Continue rebase after fixing conflicts
git rebase --continue
```

---

## Stash

```bash
# Save uncommitted changes temporarily
git stash

# Stash with a label
git stash push -m "work in progress on X"

# List all stashes
git stash list

# Apply most recent stash (keeps it in stash list)
git stash apply

# Apply and remove most recent stash
git stash pop

# Apply a specific stash
git stash apply stash@{2}

# Drop a stash
git stash drop stash@{0}
```

---

## Tags

```bash
# Create a lightweight tag
git tag v1.0.0

# Create an annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# List all tags
git tag

# Push tags to remote
git push origin --tags

# Delete a local tag
git tag -d v1.0.0

# Delete a remote tag
git push origin --delete v1.0.0
```

---

## Useful Shortcuts

```bash
# See a summary of changes between two branches
git diff main..feature/my-feature --stat

# Find which commit introduced a string
git log -S "function_name" --oneline

# Search commit messages
git log --grep="bug fix" --oneline

# Show files changed in last commit
git show --stat HEAD

# List files that have changed between two branches
git diff --name-only main..feature/my-feature

# Clean untracked files (dry run first)
git clean -n
git clean -f
```

---

## Setting Up This Project on GitHub (New Repo)

```bash
cd /Users/ananyasoni/MMM_AgenticAI

git init
git add .
git commit -m "Initial commit: MMM Intelligence Copilot"

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/mmm-intelligence-copilot.git
git branch -M main
git push -u origin main
```

### What to add to .gitignore before pushing

```bash
# Create a .gitignore
cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
*.pyo
.chroma_db/
*.egg-info/
dist/
build/
.DS_Store
EOF
```

> **Important:** Never commit your `.env` file — it contains your `GROQ_API_KEY`. The `.gitignore` above keeps it out.

---

## Common Scenarios

**I committed to the wrong branch**
```bash
git log --oneline -1          # note the commit hash
git reset HEAD~1              # undo commit, keep changes
git checkout correct-branch
git add .
git commit -m "your message"
```

**I want to pull but have uncommitted changes**
```bash
git stash
git pull
git stash pop
```

**Merge conflict — what to do**
```bash
# After git merge or git pull triggers a conflict:
# 1. Open the conflicted file — look for <<<<<<, =======, >>>>>>>
# 2. Edit the file to keep what you want
# 3. Then:
git add conflicted-file.py
git commit
```

**I accidentally staged my .env file**
```bash
git restore --staged .env
echo ".env" >> .gitignore
git add .gitignore
git commit -m "add .env to gitignore"
```
