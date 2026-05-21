# Tech Stack

## Core Framework
- Strands Agents SDK (Python) — AI agent framework
- AgentCore CLI (`agentcore`) — scaffolding, local dev, deployment, and management

## Languages
- Python (with type hints required)

## AWS Services
- Amazon Bedrock (LLM provider)
- AgentCore Runtime (agent hosting)
- AgentCore Gateway (MCP-based tool routing)
- DynamoDB (order/customer/product data)
- Bedrock Knowledge Base (return policy documents)
- Lambda (gateway tool targets)
- Cognito (authentication for gateway and UI)
- IAM (execution roles and policies)

## UI
- Streamlit (chat interface)

## Package Management
- uv (Python package manager, `uv sync` for dependency installation)
- pyproject.toml for dependency declarations

## Region
- All AWS operations target `us-west-2`

## Common Commands

```bash
# Scaffold a new project
agentcore create

# Local development server
agentcore dev

# Deploy to AgentCore Runtime
agentcore deploy

# Invoke deployed agent
agentcore invoke

# Validate configuration
agentcore validate

# Check deployment status
agentcore status

# View logs
agentcore logs --since 30m

# Sync dependencies after editing pyproject.toml
uv sync

# Run Streamlit UI
cd streamlit-ui && streamlit run streamlit_app.py --server.port 8501
```

## AgentCore Configuration Rules

- ALWAYS run `agentcore validate` after editing `agentcore.json`
- In `agentcore.json`, runtime envVars are arrays:
  ```json
  "envVars": [{ "name": "KEY", "value": "VALUE" }]
  ```
- NEVER write `${SHELL_VARIABLE}` or `${PARAM}` placeholders into `agentcore.json`. The CLI does not expand environment variables in this file — placeholders propagate verbatim into the deployed CDK stack and the runtime IAM policy, producing AccessDenied errors at invoke time. Always resolve the variable yourself first (e.g., run the lookup CLI command to get the real value) and write the literal value into `agentcore.json`.
