/**
 * Workflow Starter Script - Multiple Nodes
 * Simple script to start a new multiple-nodes workflow instance.
 */
import { Connection, Client } from '@temporalio/client';
import { multipleNodesWorkflow } from './workflow-definitions.js';
import { randomUUID } from 'crypto';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-multiple-nodes-task-queue';

/**
 * Start a new multiple-nodes workflow instance.
 */
async function startWorkflow(inputValue: number, workflowId?: string): Promise<string> {
  // Connect to Temporal server
  const connection = await Connection.connect({ address: TEMPORAL_HOST });
  const client = new Client({ connection });

  // Generate workflow ID if not provided
  const id = workflowId || `multiple-nodes-workflow-${randomUUID()}`;

  console.log(`Starting workflow with ID: ${id}`);
  console.log(`Input value: ${inputValue}`);

  // Start and wait for workflow completion
  const handle = await client.workflow.start(multipleNodesWorkflow, {
    args: [inputValue],
    taskQueue: TASK_QUEUE,
    workflowId: id,
  });

  console.log('Workflow started, waiting for result...');

  const result = await handle.result();

  console.log(`Workflow completed: ${result}`);
  return result;
}

async function main() {
  try {
    console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);

    // Example 1: Valid input
    console.log('\n=== Example 1: Valid input ===');
    await startWorkflow(15);

    // Example 2: Invalid input (should fail validation)
    console.log('\n=== Example 2: Invalid input (should fail validation) ===');
    await startWorkflow(-5);

    console.log('\n=== All examples completed ===');
  } catch (error) {
    console.error('Error executing workflow:', error);
    process.exit(1);
  }
}

main();
