/**
 * Express Workflow Starter
 * REST API to start and query workflow instances.
 */
import express, { Request, Response } from 'express';
import { Connection, Client } from '@temporalio/client';
import { singleNodeWorkflow } from './workflow-definitions.js';
import { randomUUID } from 'crypto';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-single-node-task-queue';
const PORT = 8000;

const app = express();
app.use(express.json());

// Temporal client instance
let temporalClient: Client;

/**
 * Initialize Temporal client connection
 */
async function initTemporalClient() {
  const connection = await Connection.connect({ address: TEMPORAL_HOST });
  temporalClient = new Client({ connection });
  console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);
}

/**
 * Request and Response types
 */
interface WorkflowRequest {
  input_value: number;
  workflow_id?: string;
}

interface WorkflowResponse {
  workflow_id: string;
  result: number;
  status: string;
}

/**
 * Root endpoint with API information
 */
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Single Node Workflow API',
    version: '1.0.0',
    endpoints: {
      start_workflow: '/workflow/start',
      health: '/health',
    },
  });
});

/**
 * Health check endpoint
 */
app.get('/health', async (req: Request, res: Response) => {
  try {
    if (!temporalClient) {
      throw new Error('Temporal client not initialized');
    }
    res.json({ status: 'healthy', temporal_connected: true });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Start a new workflow instance
 */
app.post('/workflow/start', async (req: Request, res: Response) => {
  try {
    const request = req.body as WorkflowRequest;

    if (typeof request.input_value !== 'number') {
      res.status(400).json({ error: 'input_value is required and must be a number' });
      return;
    }

    // Generate workflow ID if not provided
    const workflowId = request.workflow_id || `single-node-workflow-${randomUUID()}`;

    // Start and wait for workflow completion
    const handle = await temporalClient.workflow.start(singleNodeWorkflow, {
      args: [request.input_value],
      taskQueue: TASK_QUEUE,
      workflowId,
    });

    const result = await handle.result();

    const response: WorkflowResponse = {
      workflow_id: workflowId,
      result,
      status: 'completed',
    };

    res.json(response);
  } catch (error) {
    console.error('Workflow execution error:', error);
    res.status(500).json({
      error: 'Workflow execution failed',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Start the server
 */
async function main() {
  try {
    // Initialize Temporal client first
    await initTemporalClient();

    // Start Express server
    app.listen(PORT, () => {
      console.log(`API server listening on http://0.0.0.0:${PORT}`);
      console.log(`Health check: http://localhost:${PORT}/health`);
      console.log(`Start workflow: POST http://localhost:${PORT}/workflow/start`);
    });
  } catch (error) {
    console.error('Failed to start API server:', error);
    process.exit(1);
  }
}

main();
