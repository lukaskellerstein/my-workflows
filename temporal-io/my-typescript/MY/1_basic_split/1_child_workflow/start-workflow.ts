/**
 * Workflow Starter Script - Child Workflow
 * Script to start an order processing workflow
 */
import { Connection, Client } from '@temporalio/client';
import { processOrderWorkflow, type Order } from './workflow-definitions.js';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '1-basic-child-workflow-task-queue';

/**
 * Start an order processing workflow
 */
async function startWorkflow(order: Order, workflowId?: string): Promise<string> {
  // Connect to Temporal server
  const connection = await Connection.connect({ address: TEMPORAL_HOST });
  const client = new Client({ connection });

  // Generate workflow ID if not provided
  const id = workflowId || `child-workflow-${order.orderId}`;

  console.log(`Starting workflow with ID: ${id}`);
  console.log(`Order ID: ${order.orderId}`);
  console.log(`Customer: ${order.customer}`);
  console.log(`Items: ${order.items.length}`);

  // Start and wait for workflow completion
  const handle = await client.workflow.start(processOrderWorkflow, {
    args: [order],
    taskQueue: TASK_QUEUE,
    workflowId: id,
  });

  console.log('Workflow started, waiting for result...');

  const result = await handle.result();

  console.log(`\nWorkflow completed successfully!`);
  console.log(`\n${result}`);
  return result;
}

async function main() {
  try {
    console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);

    // Create a sample order
    const order: Order = {
      orderId: 'ORD-12345',
      customer: 'John Doe',
      items: [
        { product: 'Laptop', quantity: 1, price: 999.99 },
        { product: 'Mouse', quantity: 2, price: 29.99 },
        { product: 'Keyboard', quantity: 1, price: 79.99 },
      ],
    };

    await startWorkflow(order, '1-basic-child-workflow-order-12345');
  } catch (error) {
    console.error('Error executing workflow:', error);
    process.exit(1);
  }
}

main();
