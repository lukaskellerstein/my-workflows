/**
 * Example 2: Multiple Nodes Workflow
 * This demonstrates a workflow with multiple activities executed sequentially.
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

/**
 * Activity 1: Validate input
 */
export async function validateInput(value: number): Promise<boolean> {
  activityLog.info('Validating input:', { value });
  const isValid = value > 0;
  activityLog.info('Validation result:', { isValid });
  return isValid;
}

/**
 * Activity 2: Transform data
 */
export async function transformData(value: number): Promise<number> {
  activityLog.info('Transforming data:', { value });
  const result = value * 3 + 10;
  activityLog.info('Transformed result:', { result });
  return result;
}

/**
 * Activity 3: Save result
 */
export async function saveResult(value: number): Promise<string> {
  activityLog.info('Saving result:', { value });
  return `Successfully saved value: ${value}`;
}

// ============================================================================
// WORKFLOWS
// ============================================================================
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  validateInput(value: number): Promise<boolean>;
  transformData(value: number): Promise<number>;
  saveResult(value: number): Promise<string>;
}

// Proxy activities with timeout configuration
const {
  validateInput: validateInputActivity,
  transformData: transformDataActivity,
  saveResult: saveResultActivity,
} = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Workflow with multiple activity nodes executed sequentially
 */
export async function multipleNodesWorkflow(inputValue: number): Promise<string> {
  workflowLog.info('Starting workflow with input:', { inputValue });

  // Node 1: Validate input
  const isValid = await validateInputActivity(inputValue);

  if (!isValid) {
    return 'Input validation failed';
  }

  // Node 2: Transform data
  const transformed = await transformDataActivity(inputValue);

  // Node 3: Save result
  const saveMessage = await saveResultActivity(transformed);

  workflowLog.info('Workflow completed:', { saveMessage });
  return saveMessage;
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';
import { randomUUID } from 'crypto';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-multiple-nodes-task-queue';

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
        validateInput,
        transformData,
        saveResult,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Execute workflow
    const workflowId = `multiple-nodes-workflow-${randomUUID()}`;
    console.log(`Starting workflow with ID: ${workflowId}`);

    const handle = await client.workflow.start(multipleNodesWorkflow, {
      args: [42],
      taskQueue: TASK_QUEUE,
      workflowId,
    });

    console.log('Workflow started, waiting for result...');
    const result = await handle.result();

    console.log(`Workflow completed successfully!`);
    console.log(`Workflow ID: ${workflowId}`);
    console.log(`Result: ${result}`);

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
