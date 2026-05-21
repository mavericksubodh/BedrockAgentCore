---
trigger: onFileSave
fileMatchPattern: "**/pyproject.toml"
action: command
---

uv sync
