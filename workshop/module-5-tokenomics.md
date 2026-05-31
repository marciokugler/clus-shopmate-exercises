# 5. Tokenomics And Chargeback

## Goal

Use AI telemetry to answer a business question:

```text
Which student and department consumed the most tokens, and was the spend properly chargeback-tagged?
```

## Tokenomics Fields

Every app request should carry:

```text
student.id
team.name
department.name
department.cost_center
chargeback.account
```

These fields are resource attributes from `OTEL_RESOURCE_ATTRIBUTES`, not custom app code.

Token metrics come from Splunk zero-code OpenAI/OpenAI Agents instrumentation. Depending on package versions, your tenant may show names such as `gen_ai.client.token.usage`, `gen_ai.usage.input_tokens`, or `gen_ai.usage.output_tokens`. Use the token metric names visible in your Splunk tenant.

## Step 1: Run A Baseline Conversation

Send two turns in the ShopMate assistant.

```text
Turn 1: Find a waterproof jacket under $200 for a weekend hiking trip.
Turn 2: Compare the top two options and check if medium is in stock.
```

Validate:

- token counts exist
- `student.id` is present
- department and chargeback attributes are present

## Step 2: Run A Token Surge Conversation

Send a longer fictional retail conversation.

```text
Turn 1: Build a complete back-to-school shopping cart for two kids with different budgets.
Turn 2: Compare three laptop options, explain tradeoffs, and check accessory compatibility.
Turn 3: Add delivery timing constraints and return policy requirements.
Turn 4: Rewrite the recommendation as a detailed email to a parent.
Turn 5: Summarize the decision in five bullets and include estimated savings.
```

Expected result:

- token totals increase
- the conversation is more expensive than the baseline
- traces show larger prompt or completion token values

## Step 3: Run The Agent Loop Token Burn

Run the bounded loop scenario:

```text
Find waterproof trail running shoes under $40, available today, with carbon plate support, in every color, and explain all alternatives in detail.
```

Validate:

- the request returns instead of running indefinitely
- the trace shows OpenAI Agents SDK activity
- the trace shows NIM-backed LLM spans
- token totals are higher than the baseline

## Step 4: Find Your Highest-Cost Student View

In Splunk Observability Cloud:

1. Filter by `service.name=shopmate-ai` or the lab-provided ShopMate service name.
2. Filter by `student.id=<your student id>`.
3. Find token usage for your environment.
4. Split prompt tokens and completion tokens if both are available.
5. Compare baseline, token surge, and expensive multi-agent prompts.
6. Open a high-token trace.

Ask:

- Which request window used the most tokens?
- Which span or model call used the most tokens?
- Did prompt tokens or completion tokens dominate?
- Did an agent call NIM more than expected?
- Was `chargeback.account` present?

## Step 5: Class Chargeback Challenge

Now answer the class-wide question.

Group by:

```text
department.name
department.cost_center
chargeback.account
student.id
```

Find:

- highest total token student
- highest total token department
- highest average tokens per request window
- largest single trace or model call
- missing or invalid chargeback tags
- whether high usage came from normal use, token surge, retries, or bad tagging

## Step 6: Write Your Finding

Use this format:

```text
Top student:
Top department:
Top request window or trace:
Prompt tokens vs completion tokens:
Chargeback account present:
Evidence from trace:
Evidence from metrics:
Likely cause:
Recommended guardrail or operational action:
```

Examples of good recommendations:

- set a max iteration count for agent loops
- set a token budget per request
- cache repeated tool results
- fail fast on impossible catalog constraints
- review prompts that produce unusually high completion tokens

!!! success "Checkpoint"
    You can defend your answer with trace evidence, token metrics, and chargeback attributes.

## Knowledge Check

??? question "Why is request count not enough for AI chargeback?"
    One request can use many more tokens than another. Chargeback needs prompt tokens, completion tokens, model name, student, department, and conversation context.

??? question "What makes the agent-loop scenario financially important?"
    It turns an application logic problem into measurable AI spend. Without trace and token attributes, it may look like ordinary model usage.

??? question "What field shows unattributed spend?"
    `chargeback.account=unattributed`, `chargeback.valid=false`, or a rising `ai.chargeback.missing_tags` metric, depending on the app implementation.
