"""
Lambda function for DynamoDB data lookups via AgentCore Gateway.
Supports tools: order_lookup, user_lookup, product_lookup.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key

REGION = "us-west-2"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

ORDERS_TABLE = "workshop-orders"
CUSTOMERS_TABLE = "workshop-customers"
PRODUCTS_TABLE = "workshop-products"


def lambda_handler(event: dict, context) -> dict:
    """Route requests to the appropriate lookup based on bedrockAgentCoreToolName."""
    delimiter = "___"

    original_tool_name: str = context.client_context.custom["bedrockAgentCoreToolName"]
    tool_name = original_tool_name[original_tool_name.index(delimiter) + len(delimiter):]

    if tool_name == "order_lookup":
        return handle_order_lookup(event)
    elif tool_name == "user_lookup":
        return handle_user_lookup(event)
    elif tool_name == "product_lookup":
        return handle_product_lookup(event)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def handle_order_lookup(event: dict) -> dict:
    """Look up orders for a customer, optionally filtered by product_id."""
    customer_id: str = event.get("customer_id", "")
    product_id: str | None = event.get("product_id")

    table = dynamodb.Table(ORDERS_TABLE)

    if product_id:
        response = table.get_item(Key={"customer_id": customer_id, "product_id": product_id})
        item = response.get("Item")
        return {"orders": [item] if item else [], "count": 1 if item else 0}
    else:
        response = table.query(KeyConditionExpression=Key("customer_id").eq(customer_id))
        items = response.get("Items", [])
        return {"orders": items, "count": len(items)}


def handle_user_lookup(event: dict) -> dict:
    """Look up a customer by customer_id."""
    customer_id: str = event.get("customer_id", "")

    table = dynamodb.Table(CUSTOMERS_TABLE)
    response = table.get_item(Key={"customer_id": customer_id})
    item = response.get("Item")

    if item:
        return {"customer": item}
    else:
        return {"error": f"Customer {customer_id} not found"}


def handle_product_lookup(event: dict) -> dict:
    """Look up a product by product_id."""
    product_id: str = event.get("product_id", "")

    table = dynamodb.Table(PRODUCTS_TABLE)
    response = table.get_item(Key={"product_id": product_id})
    item = response.get("Item")

    if item:
        return {"product": item}
    else:
        return {"error": f"Product {product_id} not found"}
