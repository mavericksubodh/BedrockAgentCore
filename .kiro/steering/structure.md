# Project Structure

```
ReturnsRefundsAgentProject/
├── .kiro/
│   ├── settings/
│   │   └── mcp.json              # MCP server configuration (AWS docs, Strands docs)
│   └── steering/                  # AI assistant steering rules
├── AgentCoreProject/
│   ├── app/
│   │   └── CustomerAssistantAgent/
│   │       └── main.py           # Agent entry point (system prompt, tools, memory)
│   ├── agentcore/
│   │   ├── agentcore.json        # AgentCore project configuration (runtime, gateway, memory)
│   │   └── .env.local            # Local environment variables (memory ID, gateway creds)
│   ├── tool_specs/               # Gateway tool specification JSON files
│   └── pyproject.toml            # Python dependencies
├── lambda_functions/
│   ├── data_lookup/
│   │   └── handler.py            # DynamoDB lookups (orders, customers, products)
│   └── policy_retrieval/
│       └── handler.py            # Bedrock Knowledge Base policy queries
├── streamlit-ui/
│   └── streamlit_app.py          # Chat UI with Cognito auth
├── cognito_config.json           # Cognito credentials for gateway OAuth
└── lab-prompts.md                # Workshop instructions and prompts
```

## Key Conventions
- Agent code lives in `AgentCoreProject/app/<AgentName>/main.py`
- AgentCore config is in `agentcore/agentcore.json` — always run `agentcore validate` after editing
- Environment variables for runtime are defined as arrays: `"envVars": [{"name": "KEY", "value": "VALUE"}]`
- Tool implementations use the Strands `@tool` decorator pattern
- Lambda functions follow the AgentCore Gateway input/output format
