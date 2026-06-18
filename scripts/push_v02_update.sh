#!/usr/bin/env bash
set -euo pipefail

# Run from repository root after reviewing v0.2 changes.

git status
git add .
git commit -m "Update v0.2 real G1 read-only data pipeline" || true
git branch -M main
git push origin main
