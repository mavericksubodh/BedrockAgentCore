Links - https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/lab1-kiro-features/01-workshop-setup/0101-setup-kiro-on-your-device


Prompt to add persisting memory to the application
I have added a new memory using AgentCore CLI. Integrate it into app/CustomerAssistantAgent/main.py with all the fixes needed for cross-session memory retrieval to work end-to-end. Then deploy.

References:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html
- https://strandsagents.com/docs/community/session-managers/agentcore-memory/

## Setup
1. Find the new memory ID (not ARN) using `agentcore status --json` and update agentcore/.env.local
2. Add memory ID to envVars of the runtime in agentcore.json
3. Region: us-west-2, default actor_id: "administrator"
4. Read agentcore.json to find the EXACT memory namespaces and use them in retrieval_config (include both session-specific AND cross-session namespaces)

Important namespace format: use f"/users/{actor_id}/preferences" — NOT f"/users/{{{actor_id}}}/preferences" (triple braces is the common mistake)

## Memory Config
- Set `relevance_score=0.2` for all retrieval namespaces (low threshold for better recall)
- Set `batch_size=1` for immediate memory updates
- Add graceful fallback: if MEMORY_ID env var is empty, skip session_manager creation

## Code Pattern (main.py) — apply ALL of these

### No singleton agent
Do NOT cache the agent globally. The session_manager gets closed after each invocation, leaving a stale agent on warm restarts. Create a fresh agent per invocation via a `create_agent(session_id: str)` function.

### Use runtime context session_id
In the invoke entrypoint, pull the session_id from the runtime context:

```python
from bedrock_agentcore.runtime.context import BedrockAgentCoreContext

session_id = (
    getattr(context, 'session_id', None)
    or BedrockAgentCoreContext.get_session_id()
    or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
)
agent = create_agent(session_id)
Close session manager via private attribute (in finally block)
Strands stores session_manager as _session_manager (private). Use try/finally:

try:
    stream = agent.stream_async(prompt)
    async for event in stream:
        ...
finally:
    sm = getattr(agent, '_session_manager', None)
    if sm:
        sm.close()
CDK Fix (cdk-stack.ts) — REQUIRED
The @aws/agentcore-cdk L3 construct restricts RetrieveMemoryRecords with an IAM condition on bedrock-agentcore:namespace, but the Strands SDK calls the API with namespacePath which maps to a different IAM condition key. Retrieval is silently denied without this fix.

In 
cdk-stack.ts
:

Add: import * as iam from 'aws-cdk-lib/aws-iam'
After creating the AgentCoreApplication, add this block:

const application = this.application || this.node.findChild('Application') as any;
const agentEnvs = application.node.findAll().filter((c: any) => c.runtime?.role !== undefined);
for (const env of agentEnvs) {
    const role = (env as any).runtime.role as iam.IRole;
    role.addToPrincipalPolicy(new iam.PolicyStatement({
        sid: 'AllowNamespacePathRetrieval',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock-agentcore:RetrieveMemoryRecords', 'bedrock-agentcore:ListMemoryRecords'],
        resources: ['*'],
    }));
}
After all changes, run agentcore deploy.