from typing import Any
from datetime import datetime, timedelta

from strands import Agent, tool
from strands_tools import current_time
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from mcp_client.client import get_streamable_http_mcp_client
from memory.session import get_memory_session_manager

app = BedrockAgentCoreApp()
log = app.logger

# Define a Streamable HTTP MCP Client
mcp_clients = [get_streamable_http_mcp_client()]

DEFAULT_SYSTEM_PROMPT = """
You are a Returns & Refunds Assistant. Introduce yourself as such when greeting users.

The user is an administrator with access to customer data, orders, and return policies.
You help administrators:
- Check return eligibility for customer orders
- Calculate refund amounts
- Answer questions about return policies on behalf of customers

Guidelines:
- Be helpful and concise
- Always confirm order details and customer information before processing any return or refund
- Use available tools to look up data rather than making assumptions
"""


# Define a collection of tools used by the model
tools = []

# Built-in Strands tool for current date/time
tools.append(current_time)


# Mock order data
MOCK_ORDERS: dict[str, dict[str, str]] = {
    "ORD-001": {
        "order_id": "ORD-001",
        "customer_id": "C-01",
        "product_id": "P-001",
        "product_name": "iPhone 15 Pro",
        "status": "DELIVERED",
        "purchased": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "customer_id": "C-02",
        "product_id": "P-003",
        "product_name": "Kindle Paperwhite",
        "status": "DELIVERED",
        "purchased": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "customer_id": "C-01",
        "product_id": "P-005",
        "product_name": "PlayStation 5",
        "status": "SHIPPED",
        "purchased": datetime.now().strftime("%Y-%m-%d"),
    },
}


@tool
def order_lookup(order_id: str) -> str:
    """Look up order details by order ID. Returns order information including customer, product, status, and purchase date."""
    order = MOCK_ORDERS.get(order_id)
    if not order:
        return f"Order {order_id} not found."
    return (
        f"Order ID: {order['order_id']}\n"
        f"Customer: {order['customer_id']}\n"
        f"Product: {order['product_name']} ({order['product_id']})\n"
        f"Status: {order['status']}\n"
        f"Purchased: {order['purchased']}"
    )
tools.append(order_lookup)


# Mock customer data
MOCK_CUSTOMERS: dict[str, dict[str, str]] = {
    "C-01": {"user_id": "C-01", "name": "Rajesh Kumar", "country": "IN", "email": "rajesh@example.com"},
    "C-02": {"user_id": "C-02", "name": "Sarah Johnson", "country": "US", "email": "sarah@example.com"},
    "C-03": {"user_id": "C-03", "name": "James Wilson", "country": "UK", "email": "james@example.com"},
}


@tool
def user_lookup(user_id: str) -> str:
    """Retrieve customer information by user ID. Returns name, country, and email."""
    customer = MOCK_CUSTOMERS.get(user_id)
    if not customer:
        return f"Customer {user_id} not found."
    return (
        f"User ID: {customer['user_id']}\n"
        f"Name: {customer['name']}\n"
        f"Country: {customer['country']}\n"
        f"Email: {customer['email']}"
    )
tools.append(user_lookup)


# Mock product data
MOCK_PRODUCTS: dict[str, dict[str, str]] = {
    "P-001": {"product_id": "P-001", "name": "iPhone 15 Pro", "brand": "Apple", "category": "phone"},
    "P-002": {"product_id": "P-002", "name": "Kindle Paperwhite", "brand": "Amazon", "category": "e-book"},
    "P-003": {"product_id": "P-003", "name": "iPad Air", "brand": "Apple", "category": "tablet"},
}


@tool
def product_lookup(product_id: str) -> str:
    """Retrieve product information by product ID. Returns product name, brand, and category."""
    product = MOCK_PRODUCTS.get(product_id)
    if not product:
        return f"Product {product_id} not found."
    return (
        f"Product ID: {product['product_id']}\n"
        f"Name: {product['name']}\n"
        f"Brand: {product['brand']}\n"
        f"Category: {product['category']}"
    )
tools.append(product_lookup)


# Mock return policy data
MOCK_POLICIES: dict[str, dict[str, str]] = {
    "electronics": {
        "category": "electronics",
        "return_window": "30 days",
        "refund": "100% refund if unopened",
    },
    "clothing": {
        "category": "clothing",
        "return_window": "60 days",
        "refund": "Full refund",
    },
    "books": {
        "category": "books",
        "return_window": "14 days",
        "refund": "50% refund",
    },
}


@tool
def policy_retrieval(query: str) -> str:
    """Retrieve return policy information based on a query. Searches policies by category keyword."""
    query_lower = query.lower()
    for category, policy in MOCK_POLICIES.items():
        if category in query_lower:
            return (
                f"Category: {policy['category']}\n"
                f"Return Window: {policy['return_window']}\n"
                f"Refund: {policy['refund']}"
            )
    return f"No policy found matching query: {query}"
tools.append(policy_retrieval)


# Add MCP client to tools if available
for mcp_client in mcp_clients:
    if mcp_client:
        tools.append(mcp_client)


def agent_factory():
    cache = {}
    def get_or_create_agent(session_id, user_id):
        key = f"{session_id}/{user_id}"
        if key not in cache:
            # Create an agent for the given session_id and user_id
            cache[key] = Agent(
                model=load_model(),
                session_manager=get_memory_session_manager(session_id, user_id),
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                tools=tools
            )
        return cache[key]
    return get_or_create_agent
get_or_create_agent = agent_factory()


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")

    session_id = getattr(context, 'session_id', 'default-session')
    user_id = getattr(context, 'user_id', 'default-user')
    agent = get_or_create_agent(session_id, user_id)

    # Execute and format response
    stream = agent.stream_async(payload.get("prompt"))

    async for event in stream:
        # Handle Text parts of the response
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run()
