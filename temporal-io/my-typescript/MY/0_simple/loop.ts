/**
 * Example 5: Loop Workflow
 * This demonstrates a workflow that executes activities in a loop for batch processing.
 *
 * This file contains:
 * - Activity definitions
 * - Workflow definitions
 * - Worker and workflow execution logic
 */

// ============================================================================
// ACTIVITIES
// ============================================================================
import { log as activityLog } from '@temporalio/activity';

export interface Item {
  id: number;
  name: string;
  value: number;
}

/**
 * Activity to process a single item
 */
export async function processItem(item: Item): Promise<string> {
  activityLog.info('Processing item:', { name: item.name });
  // Simulate processing - Add 10%
  const processedValue = item.value * 1.1;
  return `Processed ${item.name}: $${processedValue.toFixed(2)}`;
}

/**
 * Activity to aggregate results
 */
export async function aggregateResults(results: string[]): Promise<string> {
  activityLog.info('Aggregating results:', { count: results.length });
  const totalCount = results.length;
  return `Successfully processed ${totalCount} items`;
}

// ============================================================================
// WORKFLOWS
// ============================================================================
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  processItem(item: Item): Promise<string>;
  aggregateResults(results: string[]): Promise<string>;
}

// Proxy activities with timeout configuration
const {
  processItem: processItemActivity,
  aggregateResults: aggregateResultsActivity,
} = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Workflow with loop
 * Executes activities in a loop for batch processing
 */
export async function loopWorkflow(items: Item[]): Promise<string> {
  workflowLog.info('Starting workflow:', { itemCount: items.length });

  // Loop through items and process each one
  const results: string[] = [];
  for (const item of items) {
    workflowLog.info('Processing item:', { id: item.id, name: item.name });

    const result = await processItemActivity(item);
    results.push(result);
  }

  // Aggregate all results
  const summary = await aggregateResultsActivity(results);

  workflowLog.info('Workflow completed:', { summary });

  // Return summary with all results
  return `${summary}\n${results.join('\n')}`;
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';
import { randomUUID } from 'crypto';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-loop-task-queue';

async function main() {
  try {
    // Connect to Temporal server
    const connection = await Connection.connect({ address: TEMPORAL_HOST });
    const client = new Client({ connection });
    console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);

    // Create worker connection
    const workerConnection = await NativeConnection.connect({
      address: TEMPORAL_HOST,
    });

    // Create worker
    const worker = await Worker.create({
      connection: workerConnection,
      namespace: 'default',
      taskQueue: TASK_QUEUE,
      workflowsPath: new URL(import.meta.url).pathname,
      activities: {
        processItem,
        aggregateResults,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Generate sample items
    const sampleItems: Item[] = [
      { id: 1, name: 'Item A', value: 100 },
      { id: 2, name: 'Item B', value: 200 },
      { id: 3, name: 'Item C', value: 300 },
      { id: 4, name: 'Item D', value: 400 },
      { id: 5, name: 'Item E', value: 500 },
    ];

    // Execute workflow
    const workflowId = `loop-workflow-${randomUUID()}`;
    console.log(`Starting workflow with ID: ${workflowId}`);

    const handle = await client.workflow.start(loopWorkflow, {
      args: [sampleItems],
      taskQueue: TASK_QUEUE,
      workflowId,
    });

    console.log('Workflow started, waiting for result...');
    const result = await handle.result();

    console.log(`Workflow completed successfully!`);
    console.log(`Workflow ID: ${workflowId}`);
    console.log(`Result:\n${result}`);

    // Shutdown worker
    worker.shutdown();
    await workerPromise;
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

// Only run main if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
