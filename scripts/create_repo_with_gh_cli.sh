#!/usr/bin/env bash
set -euo pipefail

# Requires GitHub CLI:
#   sudo apt install gh
#   gh auth login

REPO_NAME="${1:-g1-isaac-fastlio-nav2}"
VISIBILITY="${2:-public}"  # public or private

git init
git add .
git commit -m "Initial open-source release: G1 Isaac FAST-LIO Nav2 workflow"
git branch -M main

gh repo create "$REPO_NAME" --source=. --remote=origin --push --"$VISIBILITY"
