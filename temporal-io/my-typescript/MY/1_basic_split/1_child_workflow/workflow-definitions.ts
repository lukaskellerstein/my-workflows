/**
 * Workflow Definitions - Child Workflow
 * Demonstrates parent workflow delegating subtasks to child workflows
 */
import { proxyActivities, startChild, log as workflowLog } from '@temporalio/workflow';
import type { OrderItem } from './activities.js';

export interface Order {
  orderId: string;
  customer: string;
  items: OrderItem[];
}

// Define activity interface
export interface Activities {
  validateInventory(item: OrderItem): Promise<boolean>;
  calculateSubtotal(item: OrderItem): Promise<number>;
  processPayment(totalAmount: number, customer: string): Promise<string>;
  shipOrder(orderId: string, customer: string): Promise<string>;
}

// Proxy activities with timeout configuration
const { validateInventory, calculateSubtotal, processPayment, shipOrder } =
  proxyActivities<Activities>({
    startToCloseTimeout: '10 seconds',
  });

/**
 * Child Workflow: Process a single order item
 */
export async function processOrderItemWorkflow(item: OrderItem): Promise<number> {
  workflowLog.info('Processing item:', { product: item.product });

  // Validate inventory
  const isAvailable = await validateInventory(item);

  if (!isAvailable) {
    workflowLog.warn('Item not available:', { product: item.product });
    return 0.0;
  }

  // Calculate subtotal
  const subtotal = await calculateSubtotal(item);

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
  const paymentResult = await processPayment(totalAmount, order.customer);

  // Ship order
  const shippingResult = await shipOrder(order.orderId, order.customer);

  const result = `Order ${order.orderId} completed:
  - ${paymentResult}
  - ${shippingResult}
  - Items processed: ${order.items.length}`;

  workflowLog.info('Order processing complete:', { orderId: order.orderId });
  return result;
}
