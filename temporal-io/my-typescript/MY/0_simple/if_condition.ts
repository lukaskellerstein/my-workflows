/**
 * Example 4: Conditional (IF) Workflow
 * This demonstrates a workflow that executes different activities based on conditions.
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

export interface ProcessingInput {
  value: number;
  priority: string; // "high", "medium", "low"
}

/**
 * Fast processing activity
 */
export async function fastProcess(value: number): Promise<string> {
  activityLog.info('Fast processing:', { value });
  const result = value * 2;
  return `Fast result: ${result}`;
}

/**
 * Standard processing activity
 */
export async function standardProcess(value: number): Promise<string> {
  activityLog.info('Standard processing:', { value });
  const result = value * 3 + 5;
  return `Standard result: ${result}`;
}

/**
 * Detailed processing activity
 */
export async function detailedProcess(value: number): Promise<string> {
  activityLog.info('Detailed processing:', { value });
  const result = value * 5 + 10;
  return `Detailed result: ${result}`;
}

// ============================================================================
// WORKFLOWS
// ============================================================================
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  fastProcess(value: number): Promise<string>;
  standardProcess(value: number): Promise<string>;
  detailedProcess(value: number): Promise<string>;
}

// Proxy activities with timeout configuration
const {
  fastProcess: fastProcessActivity,
  standardProcess: standardProcessActivity,
  detailedProcess: detailedProcessActivity,
} = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Conditional workflow that executes different activities based on priority
 */
export async function conditionalWorkflow(inputData: ProcessingInput): Promise<string> {
  workflowLog.info('Starting workflow:', { value: inputData.value, priority: inputData.priority });

  let result: string;

  // Determine processing type based on priority (IF condition)
  if (inputData.priority === 'high') {
    // High priority: use fast processing
    result = await fastProcessActivity(inputData.value);
  } else if (inputData.priority === 'medium') {
    // Medium priority: use standard processing
    result = await standardProcessActivity(inputData.value);
  } else {
    // Low priority or default: use detailed processing
    result = await detailedProcessActivity(inputData.value);
  }

  workflowLog.info('Workflow completed:', { result });
  return result;
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';
import { randomUUID } from 'crypto';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-if-condition-task-queue';

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
        fastProcess,
        standardProcess,
        detailedProcess,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test different priorities
    const testCases: ProcessingInput[] = [
      { value: 10, priority: 'high' },
      { value: 20, priority: 'medium' },
      { value: 30, priority: 'low' },
    ];

    for (const testCase of testCases) {
      // Execute workflow
      const workflowId = `if-condition-workflow-${randomUUID()}`;
      console.log(`\nStarting workflow with ID: ${workflowId}`);
      console.log(`Input: value=${testCase.value}, priority=${testCase.priority}`);

      const handle = await client.workflow.start(conditionalWorkflow, {
        args: [testCase],
        taskQueue: TASK_QUEUE,
        workflowId,
      });

      console.log('Workflow started, waiting for result...');
      const result = await handle.result();

      console.log(`Workflow completed successfully!`);
      console.log(`Workflow ID: ${workflowId}`);
      console.log(`Result: ${result}`);
    }

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
