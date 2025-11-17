/**
 * Example 3: Fan-Out/Fan-In Workflow
 * This demonstrates parallel execution where tasks are started in parallel (fan-out)
 * and results are collected and aggregated (fan-in).
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

export interface DataChunk {
  chunkId: number;
  data: number[];
}

export interface ProcessingResult {
  chunkId: number;
  sum: number;
  average: number;
  maxValue: number;
  minValue: number;
}

/**
 * Process a chunk of data. This activity will run in parallel.
 * Simulates expensive computation that benefits from parallelization.
 */
export async function processChunk(chunk: DataChunk): Promise<ProcessingResult> {
  activityLog.info('Processing chunk:', { chunkId: chunk.chunkId, itemCount: chunk.data.length });

  // Simulate some computation
  const total = chunk.data.reduce((sum, val) => sum + val, 0);
  const avg = chunk.data.length > 0 ? total / chunk.data.length : 0;
  const maxVal = chunk.data.length > 0 ? Math.max(...chunk.data) : 0;
  const minVal = chunk.data.length > 0 ? Math.min(...chunk.data) : 0;

  const result: ProcessingResult = {
    chunkId: chunk.chunkId,
    sum: total,
    average: avg,
    maxValue: maxVal,
    minValue: minVal,
  };

  activityLog.info('Chunk processed:', { chunkId: chunk.chunkId, sum: total, avg: avg.toFixed(2) });
  return result;
}

/**
 * Aggregate results from all parallel tasks (Fan-In).
 */
export async function aggregateResults(results: ProcessingResult[]): Promise<string> {
  activityLog.info('Aggregating results:', { count: results.length });

  const totalSum = results.reduce((sum, r) => sum + r.sum, 0);
  const overallAvg = results.length > 0 ? results.reduce((sum, r) => sum + r.average, 0) / results.length : 0;
  const globalMax = results.length > 0 ? Math.max(...results.map(r => r.maxValue)) : 0;
  const globalMin = results.length > 0 ? Math.min(...results.map(r => r.minValue)) : 0;

  const summary = `
Aggregated Results:
  - Total chunks processed: ${results.length}
  - Total sum across all chunks: ${totalSum}
  - Overall average: ${overallAvg.toFixed(2)}
  - Global maximum: ${globalMax}
  - Global minimum: ${globalMin}
`.trim();

  return summary;
}

// ============================================================================
// WORKFLOWS
// ============================================================================
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  processChunk(chunk: DataChunk): Promise<ProcessingResult>;
  aggregateResults(results: ProcessingResult[]): Promise<string>;
}

// Proxy activities with timeout configuration
const {
  processChunk: processChunkActivity,
  aggregateResults: aggregateResultsActivity,
} = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Fan-Out/Fan-In workflow
 * Demonstrates parallel execution pattern where:
 * - Fan-Out: Multiple tasks are started in parallel
 * - Fan-In: Results from parallel tasks are collected and aggregated
 */
export async function fanOutFanInWorkflow(data: number[], chunkSize: number = 10): Promise<string> {
  workflowLog.info('Starting Fan-Out/Fan-In workflow:', { itemCount: data.length });

  // Step 1: Split data into chunks (preparation for fan-out)
  const chunks: DataChunk[] = [];
  for (let i = 0; i < data.length; i += chunkSize) {
    const chunkData = data.slice(i, i + chunkSize);
    chunks.push({ chunkId: chunks.length, data: chunkData });
  }

  workflowLog.info('Split data into chunks:', { chunkCount: chunks.length });

  // Step 2: FAN-OUT - Process all chunks in parallel
  workflowLog.info('FAN-OUT: Starting parallel processing');

  // Use Promise.all to execute activities in parallel
  const chunkResults = await Promise.all(
    chunks.map(chunk => processChunkActivity(chunk))
  );

  workflowLog.info('FAN-OUT completed:', { resultCount: chunkResults.length });

  // Step 3: FAN-IN - Aggregate all results
  workflowLog.info('FAN-IN: Aggregating results');

  const aggregated = await aggregateResultsActivity(chunkResults);

  workflowLog.info('Workflow completed');
  return aggregated;
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';
import { randomUUID } from 'crypto';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-fan-out-fan-in-task-queue';

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
        processChunk,
        aggregateResults,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Generate sample data
    const sampleData = Array.from({ length: 50 }, (_, i) => i + 1);

    // Execute workflow
    const workflowId = `fan-out-fan-in-workflow-${randomUUID()}`;
    console.log(`Starting workflow with ID: ${workflowId}`);

    const handle = await client.workflow.start(fanOutFanInWorkflow, {
      args: [sampleData, 10],
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
