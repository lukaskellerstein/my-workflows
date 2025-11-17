/**
 * Activity Definitions - Child Workflow
 * Activities for processing orders
 */
import { log as activityLog } from '@temporalio/activity';

export interface OrderItem {
  product: string;
  quantity: number;
  price: number;
}

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
