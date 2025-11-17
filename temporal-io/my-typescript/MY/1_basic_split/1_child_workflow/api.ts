/**
 * Express Workflow Starter - Child Workflow
 * REST API to start and manage order processing workflows
 */
import express, { Request, Response } from 'express';
import { Connection, Client } from '@temporalio/client';
import { processOrderWorkflow, type Order } from './workflow-definitions.js';
import type { OrderItem } from './activities.js';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '1-basic-child-workflow-task-queue';
const PORT = 8002;

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
interface OrderRequest {
  order_id: string;
  customer: string;
  items: OrderItem[];
  workflow_id?: string;
}

interface WorkflowResponse {
  workflow_id: string;
  order_id: string;
  result: string;
  status: string;
}

interface WorkflowInfo {
  description: string;
  workflow_types: string[];
  process_flow: string[];
}

/**
 * Root endpoint with API information
 */
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Child Workflow API',
    version: '1.0.0',
    description: 'Order processing with parent and child workflows',
    endpoints: {
      start_order: '/order/start',
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
 * Get information about the workflow
 */
app.get('/workflow/info', (req: Request, res: Response) => {
  const info: WorkflowInfo = {
    description: 'Order processing with parent and child workflows',
    workflow_types: ['Parent: ProcessOrderWorkflow', 'Child: ProcessOrderItemWorkflow'],
    process_flow: [
      '1. Parent workflow receives order with multiple items',
      '2. Parent spawns child workflow for each item',
      '3. Each child workflow: validates inventory and calculates subtotal',
      '4. Parent collects all subtotals and calculates total',
      '5. Parent processes payment and ships order',
    ],
  };
  res.json(info);
});

/**
 * Start a new order processing workflow
 */
app.post('/order/start', async (req: Request, res: Response) => {
  try {
    const request = req.body as OrderRequest;

    // Validate request
    if (!request.order_id || !request.customer || !request.items || request.items.length === 0) {
      res.status(400).json({
        error: 'Missing required fields: order_id, customer, and items (at least 1) are required',
      });
      return;
    }

    // Validate items
    for (const item of request.items) {
      if (!item.product || !item.quantity || !item.price) {
        res.status(400).json({
          error: 'Each item must have product, quantity, and price',
        });
        return;
      }
      if (item.quantity <= 0 || item.price <= 0) {
        res.status(400).json({
          error: 'Quantity and price must be positive numbers',
        });
        return;
      }
    }

    // Generate workflow ID if not provided
    const workflowId = request.workflow_id || `child-workflow-${request.order_id}`;

    // Create order object
    const order: Order = {
      orderId: request.order_id,
      customer: request.customer,
      items: request.items,
    };

    // Start and wait for workflow completion
    const handle = await temporalClient.workflow.start(processOrderWorkflow, {
      args: [order],
      taskQueue: TASK_QUEUE,
      workflowId,
    });

    const result = await handle.result();

    const response: WorkflowResponse = {
      workflow_id: workflowId,
      order_id: request.order_id,
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
      console.log(`Start order: POST http://localhost:${PORT}/order/start`);
      console.log('');
      console.log('Example request:');
      console.log(`  curl -X POST http://localhost:${PORT}/order/start \\`);
      console.log(`    -H "Content-Type: application/json" \\`);
      console.log(`    -d '{`);
      console.log(`      "order_id": "ORD-12345",`);
      console.log(`      "customer": "John Doe",`);
      console.log(`      "items": [`);
      console.log(`        {"product": "Laptop", "quantity": 1, "price": 999.99},`);
      console.log(`        {"product": "Mouse", "quantity": 2, "price": 29.99}`);
      console.log(`      ]`);
      console.log(`    }'`);
    });
  } catch (error) {
    console.error('Failed to start API server:', error);
    process.exit(1);
  }
}

main();
