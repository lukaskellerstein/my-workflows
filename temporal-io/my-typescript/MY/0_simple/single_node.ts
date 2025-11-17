/**
 * Example 1: Single Node Workflow
 * This demonstrates the simplest possible workflow with a single activity.
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
 * Single activity that processes data
 */
export async function processData(inputValue: number): Promise<number> {
  activityLog.info('Processing data:', { inputValue });
  const result = inputValue * 2;
  activityLog.info('Result:', { result });
  return result;
}

// ============================================================================
// WORKFLOWS
// ============================================================================
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  processData(inputValue: number): Promise<number>;
}

// Proxy activities with timeout configuration
const { processData: processDataActivity } = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Simple workflow that executes a single activity
 */
export async function singleNodeWorkflow(inputValue: number): Promise<number> {
  workflowLog.info('Starting workflow with input:', { inputValue });

  // Execute single activity
  const result = await processDataActivity(inputValue);

  workflowLog.info('Workflow completed with result:', { result });
  return result;
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';
import { randomUUID } from 'crypto';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-single-node-task-queue';

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
        processData,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Execute workflow
    const workflowId = `single-node-workflow-${randomUUID()}`;
    console.log(`Starting workflow with ID: ${workflowId}`);

    const handle = await client.workflow.start(singleNodeWorkflow, {
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
