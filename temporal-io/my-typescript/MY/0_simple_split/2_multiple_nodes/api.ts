/**
 * Express Workflow Starter - Multiple Nodes
 * REST API to start and query multiple-nodes workflow instances.
 */
import express, { Request, Response } from 'express';
import { Connection, Client } from '@temporalio/client';
import { multipleNodesWorkflow } from './workflow-definitions.js';
import { randomUUID } from 'crypto';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-multiple-nodes-task-queue';
const PORT = 8001;

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
  result: string;
  status: string;
}

interface WorkflowSteps {
  description: string;
  steps: string[];
}

/**
 * Root endpoint with API information
 */
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Multiple Nodes Workflow API',
    version: '1.0.0',
    description: 'Multi-step workflow with validation, transformation, and saving',
    endpoints: {
      start_workflow: '/workflow/start',
      workflow_info: '/workflow/info',
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
 * Get information about the workflow steps
 */
app.get('/workflow/info', (req: Request, res: Response) => {
  const info: WorkflowSteps = {
    description: 'Sequential multi-step workflow processing',
    steps: [
      '1. Validate Input - Check if input value is positive',
      '2. Transform Data - Apply transformation (value * 3 + 10)',
      '3. Save Result - Save the transformed value',
    ],
  };
  res.json(info);
});

/**
 * Start a new workflow instance
 *
 * The workflow executes three sequential activities:
 * 1. Validate the input (must be positive)
 * 2. Transform the data
 * 3. Save the result
 */
app.post('/workflow/start', async (req: Request, res: Response) => {
  try {
    const request = req.body as WorkflowRequest;

    if (typeof request.input_value !== 'number') {
      res.status(400).json({ error: 'input_value is required and must be a number' });
      return;
    }

    // Generate workflow ID if not provided
    const workflowId = request.workflow_id || `multiple-nodes-workflow-${randomUUID()}`;

    // Start and wait for workflow completion
    const handle = await temporalClient.workflow.start(multipleNodesWorkflow, {
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
      console.log(`Workflow info: http://localhost:${PORT}/workflow/info`);
      console.log(`Start workflow: POST http://localhost:${PORT}/workflow/start`);
      console.log('');
      console.log('Example request:');
      console.log(`  curl -X POST http://localhost:${PORT}/workflow/start \\`);
      console.log(`    -H "Content-Type: application/json" \\`);
      console.log(`    -d '{"input_value": 15}'`);
    });
  } catch (error) {
    console.error('Failed to start API server:', error);
    process.exit(1);
  }
}

main();
