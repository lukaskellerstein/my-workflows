/**
 * Activity Definitions - Human in the Loop
 * Activities for expense validation, notifications, and processing
 */
import { log as activityLog } from '@temporalio/activity';

export interface ExpenseRequest {
  employee: string;
  amount: number;
  category: string;
  description: string;
}

export interface EmployeeNotification {
  request: ExpenseRequest;
  status: string;
}

/**
 * Validate expense request
 */
export async function validateExpense(request: ExpenseRequest): Promise<boolean> {
  activityLog.info('Validating expense request:', { employee: request.employee });
  // Validate expense rules
  if (request.amount <= 0) {
    return false;
  }
  if (request.amount > 100000) {
    // Max limit
    return false;
  }
  return true;
}

/**
 * Notify approver about pending expense
 */
export async function notifyApprover(request: ExpenseRequest): Promise<string> {
  activityLog.info('Notifying approver:', { amount: request.amount, employee: request.employee });
  // In real scenario: send email, Slack message, etc.
  return `Notification sent to approver for ${request.employee}'s expense`;
}

/**
 * Process approved expense
 */
export async function processApprovedExpense(request: ExpenseRequest): Promise<string> {
  activityLog.info('Processing approved expense:', { amount: request.amount });
  // In real scenario: update accounting system, trigger payment
  return `Expense of $${request.amount} processed for ${request.employee}`;
}

/**
 * Notify employee about decision
 */
export async function notifyEmployee(notification: EmployeeNotification): Promise<string> {
  activityLog.info('Notifying employee:', {
    employee: notification.request.employee,
    status: notification.status,
  });
  // In real scenario: send email to employee
  return `Employee ${notification.request.employee} notified: ${notification.status}`;
}
