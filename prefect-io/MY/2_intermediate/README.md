# 2_advanced - Advanced Prefect Patterns

This folder demonstrates advanced error handling and retry patterns in Prefect.

## Examples

### 1. Retry Patterns (`01_retry_patterns.py`)

Various retry strategies for handling transient failures.

**Demonstrates:**

- **Basic Retry**: Simple retry with fixed delay
- **Exponential Backoff**: Increasing delays between retries (1s, 4s, 10s)
- **Conditional Retry**: Retry only on specific exception types
- **Retry with Fallback**: Try primary source, fall back to secondary on failure

**Key Concepts:**

```python
@task(retries=3, retry_delay_seconds=2)
def basic_retry_task():
    pass

@task(retries=3, retry_delay_seconds=[1, 4, 10])
def exponential_backoff_task():
    pass

@task(retries=2, retry_condition_fn=should_retry_fn)
def conditional_retry_task():
    pass
```

**Run:**

```bash
python 01_retry_patterns.py
```

### 2. Error Handling (`02_error_handling.py`)

Comprehensive error handling strategies.

**Demonstrates:**

- **Try-Except Pattern**: Handle errors in flow with try-except blocks
- **Graceful Degradation**: Continue processing despite some failures
- **State-Based Handling**: Check task states and handle failures accordingly
- **Custom Error Responses**: Return error objects instead of raising exceptions

**Key Patterns:**

- Process all items even if some fail
- Aggregate success/failure statistics
- Use Prefect states to inspect task results
- Design fault-tolerant workflows

**Run:**

```bash
python 02_error_handling.py
```

## Use Cases

### Retry Patterns

- API calls with rate limiting
- Network requests that might timeout
- Database operations with temporary locks
- External service integrations

### Error Handling

- Batch processing where some items might fail
- Data pipelines that must complete despite errors
- Multi-step workflows with failure recovery
- Monitoring and alerting based on error rates

## Best Practices

1. **Retry for Transient Failures**: Use retries for temporary issues (network, rate limits)
2. **Don't Retry Permanent Failures**: Avoid retrying validation errors or bad input
3. **Use Exponential Backoff**: Prevent overwhelming failing services
4. **Log Extensively**: Record failures for debugging and monitoring
5. **Set Reasonable Timeouts**: Don't retry indefinitely
6. **Graceful Degradation**: Design systems that partially succeed

# 3_concurrency - Parallel Execution Patterns

This folder demonstrates various concurrency and parallel execution patterns in Prefect.

## Examples

### 1. Parallel Execution (`01_parallel_execution.py`)

Comprehensive guide to parallel task execution.

**Demonstrates:**

- **Sequential vs Parallel**: Compare performance between sequential and parallel execution
- **Task Mapping**: Use `.map()` to execute tasks in parallel
- **Thread Pool Runner**: Configure thread pool for concurrent execution
- **Async/Await**: Use async tasks for concurrent I/O operations
- **Mixed Patterns**: Combine parallel and sequential execution

**Key Patterns:**

**Sequential Execution:**

```python
for item in items:
    result = task(item)  # One at a time
```

**Parallel with Map:**

```python
results = task.map(items)  # All at once
```

**Thread Pool:**

```python
@flow(task_runner=ThreadPoolTaskRunner(max_workers=10))
def my_flow():
    results = task.map(items)
```

**Async/Await:**

```python
@task
async def async_task():
    async with httpx.AsyncClient() as client:
        return await client.get(url)

@flow
async def async_flow():
    futures = [async_task.submit(url) for url in urls]
    results = [await future for future in futures]
```

**Run:**

```bash
python 01_parallel_execution.py
```

## Performance Comparison

| Pattern        | 5 items @ 0.5s each    | Speedup |
| -------------- | ---------------------- | ------- |
| Sequential     | ~2.5 seconds           | 1x      |
| Parallel (map) | ~0.5 seconds           | 5x      |
| Thread Pool    | ~0.5 seconds           | 5x      |
| Async          | ~1.0 second (with I/O) | 5x      |

## When to Use Each Pattern

### Sequential Execution

- Tasks must run in specific order
- Tasks depend on previous results
- Working with non-thread-safe resources
- Debugging and development

### Parallel with Map

- Independent tasks that don't depend on each other
- I/O-bound operations (API calls, file reads)
- Batch processing of similar items
- When order doesn't matter

### Thread Pool Runner

- Need fine control over concurrency
- Limited resources (database connections)
- CPU-bound tasks (with GIL limitations)
- Mixed I/O and computation

### Async/Await

- High-concurrency I/O operations
- Network requests (HTTP, websockets)
- Database queries (with async drivers)
- Best performance for I/O-bound work

## Use Cases

- **ETL Pipelines**: Extract from multiple sources in parallel
- **API Integration**: Fetch data from multiple endpoints concurrently
- **Batch Processing**: Process large datasets efficiently
- **Web Scraping**: Scrape multiple pages simultaneously
- **Data Validation**: Validate multiple files/records in parallel

## Best Practices

1. **Choose Right Pattern**: Match concurrency pattern to workload type
2. **Limit Concurrency**: Don't overwhelm external services (use max_workers)
3. **Handle Errors**: One task failure shouldn't stop all tasks
4. **Monitor Resources**: Watch memory, connections, and rate limits
5. **Test Performance**: Measure actual speedup with your workload

## Next Steps

After mastering concurrency, explore:

- `../4_human_in_loop/` - Workflows with human approval
- `../5_AI/` - AI and LLM integration
