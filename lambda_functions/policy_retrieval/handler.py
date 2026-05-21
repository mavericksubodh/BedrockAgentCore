"""
Lambda function for retrieving return policies from Bedrock Knowledge Base
via AgentCore Gateway.
"""

import json
import boto3

REGION = "us-west-2"
SSM_KB_PARAM = "/app/workshop/kb/knowledge-base-id"

ssm_client = boto3.client("ssm", region_name=REGION)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)

# Cache the Knowledge Base ID across warm invocations
_knowledge_base_id: str | None = None


def get_knowledge_base_id() -> str:
    """Retrieve the Knowledge Base ID from SSM Parameter Store (cached)."""
    global _knowledge_base_id
    if _knowledge_base_id is None:
        response = ssm_client.get_parameter(Name=SSM_KB_PARAM)
        _knowledge_base_id = response["Parameter"]["Value"]
    return _knowledge_base_id


def lambda_handler(event: dict, context) -> dict:
    """Retrieve return policy information from Bedrock Knowledge Base."""
    delimiter = "___"

    original_tool_name: str = context.client_context.custom["bedrockAgentCoreToolName"]
    tool_name = original_tool_name[original_tool_name.index(delimiter) + len(delimiter):]

    query: str = event.get("query", "")
    if not query:
        return {"error": "Missing required parameter: query"}

    kb_id = get_knowledge_base_id()

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": query},
    )

    results = []
    for result in response.get("retrievalResults", []):
        content = result.get("content", {}).get("text", "")
        score = result.get("score", 0.0)
        metadata = result.get("metadata", {})
        source = result.get("location", {}).get("s3Location", {}).get("uri", "")

        results.append({
            "text": content,
            "score": score,
            "source": source,
            "country": metadata.get("country", ""),
        })

    return {
        "policy_results": results,
        "count": len(results),
        "query": query,
    }
