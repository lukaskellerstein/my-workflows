/**
 * Workflow Starter Script
 * Directly starts a workflow instance using the Temporal client.
 */
import { Connection, Client } from '@temporalio/client';
import { singleNodeWorkflow } from './workflow-definitions.js';
import { randomUUID } from 'crypto';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-single-node-task-queue';

async function main() {
  try {
    // Connect to Temporal server
    const connection = await Connection.connect({ address: TEMPORAL_HOST });
    const client = new Client({ connection });

    console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);

    // Generate workflow ID
    const workflowId = `single-node-workflow-${randomUUID()}`;

    console.log(`Starting workflow with ID: ${workflowId}`);

    // Start and wait for workflow completion
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
  } catch (error) {
    console.error('Error executing workflow:', error);
    process.exit(1);
  }
}

main();
