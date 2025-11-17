/**
 * Worker Script - Multiple Nodes
 * Runs the Temporal worker that processes multiple-node workflow and activity tasks.
 */
import { NativeConnection, Worker } from '@temporalio/worker';
import * as activities from './activities.js';
import { fileURLToPath } from 'url';
import path from 'path';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-multiple-nodes-task-queue';

async function main() {
  try {
    // Connect to Temporal server
    const connection = await NativeConnection.connect({
      address: TEMPORAL_HOST,
    });
    console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);

    // Create and run worker
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);

    const worker = await Worker.create({
      connection,
      namespace: 'default',
      taskQueue: TASK_QUEUE,
      workflowsPath: path.join(__dirname, 'workflow-definitions.js'),
      activities,
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);
    console.log('Registered activities: validateInput, transformData, saveResult');
    console.log('Press Ctrl+C to stop the worker');

    // Run the worker
    await worker.run();
  } catch (error) {
    console.error('Worker error:', error);
    process.exit(1);
  }
}

main();
