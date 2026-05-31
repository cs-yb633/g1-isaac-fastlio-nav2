#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   1. Create an empty GitHub repository in the browser, for example:
#      https://github.com/<your-name>/g1-isaac-fastlio-nav2
#   2. Replace YOUR_GITHUB_USER below.
#   3. Run this script from the repository root.

GITHUB_USER="YOUR_GITHUB_USER"
REPO_NAME="g1-isaac-fastlio-nav2"
REMOTE_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"

if [ "$GITHUB_USER" = "YOUR_GITHUB_USER" ]; then
  echo "Please edit scripts/push_to_github_template.sh and set GITHUB_USER first."
  exit 1
fi

git init
git add .
git commit -m "Initial open-source release: G1 Isaac FAST-LIO Nav2 workflow"
git branch -M main
git remote add origin "$REMOTE_URL"
git push -u origin main
