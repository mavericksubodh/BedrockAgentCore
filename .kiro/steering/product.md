# Product Overview

This is a Returns & Refunds Assistant workshop project built with AWS Strands Agents SDK and the AgentCore CLI.

The agent helps administrators check return eligibility, calculate refund amounts, look up orders/customers/products, and answer questions about return policies on behalf of customers.

Key capabilities:
- Order, customer, and product lookups (via DynamoDB through AgentCore Gateway)
- Return policy retrieval (via Bedrock Knowledge Base through AgentCore Gateway)
- Persistent memory for user preferences across sessions
- Web chat UI via Streamlit with Cognito authentication
- Deployed to AWS AgentCore Runtime
