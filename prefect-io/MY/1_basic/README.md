# 1_basic - Child Workflows & Human Interaction

This folder demonstrates fundamental workflow composition and human interaction patterns in Prefect.

## Examples

### 1. Child Workflow (`01_child_workflow.py`)
Comprehensive example of parent-child workflow relationships.

**Demonstrates:**
- **Child Flows**: Flows that are called by other flows
- **Parent Flow**: Orchestrator flow that manages multiple child flows
- **Workflow Composition**: Building complex workflows from simpler, reusable flows
- **Data Flow**: Passing data between parent and child flows
- **Multiple Child Flows**: Running multiple child flows in sequence or parallel

**Key Concepts:**

1. **Basic Parent-Child Pattern**
   - Parent flow calls child flows like regular Python functions
   - Each child flow is independent and reusable
   - Data flows naturally from parent → child → parent

2. **Example Structure**
   ```
   Parent Flow
   ├── Validation Flow (child)
   │   └── validate_records task
   ├── Processing Flow (child)
   │   └── calculate_statistics task
   └── Storage Flow (child)
       └── save_to_database task
   ```

3. **Multi-Department Example**
   - Shows parallel processing of multiple child flows
   - Each department processed by its own child flow instance
   - Results aggregated in parent flow

**Run:**
```bash
python 01_child_workflow.py
```

### 2. Human in the Loop (`02_human_in_loop.py`)
Workflows that require human approval or input before proceeding.

**Demonstrates:**
- **Simple Approval**: Basic approval pattern
- **Conditional Approval**: Approval only when threshold exceeded
- **Multi-Step Approval**: Multiple approval gates in workflow
- **Retry Pattern**: Waiting for approval with retries

**Key Pattern:**
```python
@flow
def approval_flow():
    # 1. Request approval
    request_id = request_approval(details)

    # 2. Wait for human response (with retries)
    approval = wait_for_approval(request_id)

    # 3. Act based on approval
    if approval["approved"]:
        process_data()
    else:
        cancel_operation()
```

**Run:**
```bash
python 02_human_in_loop.py
```

## Benefits of These Patterns

### Child Workflows
1. **Reusability**: Child flows can be called from multiple parent flows
2. **Modularity**: Each flow has a single responsibility
3. **Observability**: Each flow and task tracked independently in Prefect UI
4. **Testing**: Child flows can be tested in isolation
5. **Composition**: Build complex workflows from simple building blocks

### Human-in-the-Loop
1. **Controlled Automation**: Critical actions require human approval
2. **Compliance**: Meet regulatory requirements for human review
3. **Safety**: Prevent automated mistakes in production
4. **Flexibility**: Workflows can pause and resume
5. **Audit Trail**: Track who approved what and when

## Use Cases

### Child Workflows
- **Multi-stage Pipelines**: ETL with distinct validation, processing, and storage stages
- **Multi-tenant Processing**: Process data for multiple customers/departments
- **Conditional Workflows**: Call different child flows based on conditions
- **Iterative Processing**: Call child flows in loops for batch processing

### Human-in-the-Loop
- **Deployment Workflows**: Require approval before deploying to production
- **Financial Operations**: Large transactions need authorization
- **Data Operations**: Destructive operations require confirmation
- **Compliance Workflows**: Regulatory requirements mandate human review

## Production Integration

For production use of human-in-the-loop workflows, integrate with:

### Email-Based Approval
- Send email with approval links
- Links trigger webhook to approve/reject
- Flow polls for approval status

### Slack Integration
- Post message with approve/reject buttons
- Button click triggers API call
- Flow waits for response

### Web Form
- Create approval record in database
- Generate approval URL
- Flow polls database for decision

### Prefect Features
- Use Prefect blocks for state management
- Trigger continuation flows on approval
- Leverage Prefect webhooks and automations

## Next Steps

After mastering these basics, explore:
- `../2_advanced/` - Error handling and retry patterns
- `../3_concurrency/` - Parallel execution patterns
- `../4_human_in_loop/` - More advanced approval workflows
- `../5_AI/` - AI and LLM integration
