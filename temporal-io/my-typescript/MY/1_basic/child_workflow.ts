/**
 * Example: Child Workflow
 * This demonstrates how to use child workflows for modular, reusable workflow components.
 * Parent workflow delegates subtasks to child workflows.
 *
 * This file contains:
 * - Data types for Order and OrderItem
 * - Activities for order processing
 * - Child workflow for processing individual items
 * - Parent workflow that orchestrates multiple child workflows
 * - Worker and workflow execution logic
 */

// ============================================================================
// DATA TYPES
// ============================================================================

export interface OrderItem {
  product: string;
  quantity: number;
  price: number;
}

export interface Order {
  orderId: string;
  customer: string;
  items: OrderItem[];
}

// ============================================================================
// ACTIVITIES
// ============================================================================
import { log as activityLog } from '@temporalio/activity';

/**
 * Validate inventory for an item
 */
export async function validateInventory(item: OrderItem): Promise<boolean> {
  activityLog.info('Validating inventory for:', { product: item.product });
  // Simulate inventory check
  return true;
}

/**
 * Calculate subtotal for an item
 */
export async function calculateSubtotal(item: OrderItem): Promise<number> {
  activityLog.info('Calculating subtotal for:', { product: item.product });
  return item.quantity * item.price;
}

/**
 * Process payment for total amount
 */
export async function processPayment(totalAmount: number, customer: string): Promise<string> {
  activityLog.info('Processing payment:', { amount: totalAmount, customer });
  // Simulate payment processing
  return `Payment successful: $${totalAmount.toFixed(2)}`;
}

/**
 * Ship order to customer
 */
export async function shipOrder(orderId: string, customer: string): Promise<string> {
  activityLog.info('Shipping order:', { orderId, customer });
  // Simulate shipping
  return `Order ${orderId} shipped to ${customer}`;
}

// ============================================================================
// WORKFLOWS
// ============================================================================
import { proxyActivities, startChild, log as workflowLog } from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  validateInventory(item: OrderItem): Promise<boolean>;
  calculateSubtotal(item: OrderItem): Promise<number>;
  processPayment(totalAmount: number, customer: string): Promise<string>;
  shipOrder(orderId: string, customer: string): Promise<string>;
}

// Proxy activities with timeout configuration
const {
  validateInventory: validateInventoryActivity,
  calculateSubtotal: calculateSubtotalActivity,
  processPayment: processPaymentActivity,
  shipOrder: shipOrderActivity,
} = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Child Workflow: Process a single order item
 */
export async function processOrderItemWorkflow(item: OrderItem): Promise<number> {
  workflowLog.info('Processing item:', { product: item.product });

  // Validate inventory
  const isAvailable = await validateInventoryActivity(item);

  if (!isAvailable) {
    workflowLog.warn('Item not available:', { product: item.product });
    return 0.0;
  }

  // Calculate subtotal
  const subtotal = await calculateSubtotalActivity(item);

  workflowLog.info('Item processed:', { product: item.product, subtotal });
  return subtotal;
}

/**
 * Parent Workflow: Process entire order using child workflows
 */
export async function processOrderWorkflow(order: Order): Promise<string> {
  workflowLog.info('Processing order:', { orderId: order.orderId, customer: order.customer });

  // Process each item using child workflows
  const subtotals: number[] = [];

  for (const item of order.items) {
    workflowLog.info('Starting child workflow for:', { product: item.product });

    // Execute child workflow for each item
    const childHandle = await startChild(processOrderItemWorkflow, {
      workflowId: `${order.orderId}-item-${item.product}`,
      args: [item],
    });

    const subtotal = await childHandle.result();
    subtotals.push(subtotal);
  }

  // Calculate total
  const totalAmount = subtotals.reduce((sum, val) => sum + val, 0);
  workflowLog.info('Total amount:', { total: totalAmount });

  // Process payment
  const paymentResult = await processPaymentActivity(totalAmount, order.customer);

  // Ship order
  const shippingResult = await shipOrderActivity(order.orderId, order.customer);

  const result = `Order ${order.orderId} completed:
  - ${paymentResult}
  - ${shippingResult}
  - Items processed: ${order.items.length}`;

  workflowLog.info('Order processing complete:', { orderId: order.orderId });
  return result;
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '1-basic-child-workflow-task-queue';

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
        validateInventory,
        calculateSubtotal,
        processPayment,
        shipOrder,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

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

    // Execute the parent workflow
    const workflowId = '1-basic-child-workflow-order-12345';
    console.log(`\nStarting workflow with ID: ${workflowId}`);

    const handle = await client.workflow.start(processOrderWorkflow, {
      args: [order],
      taskQueue: TASK_QUEUE,
      workflowId,
    });

    console.log('Workflow started, waiting for result...');
    const result = await handle.result();

    console.log(`\nWorkflow completed successfully!`);
    console.log(`\n${result}`);

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
