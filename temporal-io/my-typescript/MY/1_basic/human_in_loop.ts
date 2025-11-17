/**
 * Example: Human in the Loop
 * This demonstrates workflows that require human approval or decision-making.
 * The workflow pauses and waits for human input via signals before continuing.
 *
 * This file contains:
 * - Data types for expense requests and approval decisions
 * - Activities for validation, notifications, and processing
 * - Workflow with signal handlers for approval/rejection
 * - Worker and workflow execution with multiple scenarios
 */

// ============================================================================
// DATA TYPES
// ============================================================================

export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  TIMEOUT = 'timeout',
}

export interface ExpenseRequest {
  employee: string;
  amount: number;
  category: string;
  description: string;
}

export interface ApprovalDecision {
  approved: boolean;
  approver: string;
  comments: string;
}

export interface EmployeeNotification {
  request: ExpenseRequest;
  status: string;
}

// ============================================================================
// ACTIVITIES
// ============================================================================
import { log as activityLog } from '@temporalio/activity';

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

// ============================================================================
// WORKFLOWS
// ============================================================================
import {
  proxyActivities,
  defineSignal,
  defineQuery,
  setHandler,
  condition,
  log as workflowLog,
} from '@temporalio/workflow';

// Define activity interface
export interface Activities {
  validateExpense(request: ExpenseRequest): Promise<boolean>;
  notifyApprover(request: ExpenseRequest): Promise<string>;
  processApprovedExpense(request: ExpenseRequest): Promise<string>;
  notifyEmployee(notification: EmployeeNotification): Promise<string>;
}

// Proxy activities with timeout configuration
const {
  validateExpense: validateExpenseActivity,
  notifyApprover: notifyApproverActivity,
  processApprovedExpense: processApprovedExpenseActivity,
  notifyEmployee: notifyEmployeeActivity,
} = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

// Define signals
export const approveSignal = defineSignal<[ApprovalDecision]>('approve');
export const rejectSignal = defineSignal<[ApprovalDecision]>('reject');

// Define queries
export const getStatusQuery = defineQuery<string>('getStatus');

/**
 * Workflow with human approval
 */
export async function expenseApprovalWorkflow(request: ExpenseRequest): Promise<string> {
  let approvalStatus = ApprovalStatus.PENDING;
  let approvalDecision: ApprovalDecision | null = null;

  // Set up signal handlers
  setHandler(approveSignal, (decision: ApprovalDecision) => {
    workflowLog.info('Approval received from:', { approver: decision.approver });
    approvalStatus = ApprovalStatus.APPROVED;
    approvalDecision = decision;
  });

  setHandler(rejectSignal, (decision: ApprovalDecision) => {
    workflowLog.info('Rejection received from:', { approver: decision.approver });
    approvalStatus = ApprovalStatus.REJECTED;
    approvalDecision = decision;
  });

  // Set up query handler
  setHandler(getStatusQuery, () => approvalStatus);

  workflowLog.info('Expense approval workflow started:', {
    employee: request.employee,
    amount: request.amount,
  });

  // Step 1: Validate expense
  const isValid = await validateExpenseActivity(request);

  if (!isValid) {
    workflowLog.warn('Expense validation failed');
    return 'Expense request rejected: Invalid request';
  }

  // Step 2: Check if auto-approval is possible (e.g., small amounts)
  if (request.amount <= 100) {
    workflowLog.info('Auto-approved: Amount below threshold');
    approvalStatus = ApprovalStatus.APPROVED;
    approvalDecision = {
      approved: true,
      approver: 'Auto-Approval System',
      comments: 'Amount below $100 threshold',
    };
  } else {
    // Step 3: Notify approver - Human intervention required
    await notifyApproverActivity(request);

    workflowLog.info('Waiting for human approval...');

    // Wait for approval signal (with timeout)
    const approved = await condition(
      () => approvalStatus !== ApprovalStatus.PENDING,
      '24 hours' // 24-hour approval window
    );

    if (!approved) {
      workflowLog.warn('Approval timeout - auto-rejecting');
      approvalStatus = ApprovalStatus.TIMEOUT;
      approvalDecision = {
        approved: false,
        approver: 'System',
        comments: 'No response within 24 hours',
      };
    }
  }

  // Step 4: Process based on approval decision
  if (approvalStatus === ApprovalStatus.APPROVED && approvalDecision) {
    // Process the expense
    const processResult = await processApprovedExpenseActivity(request);

    // Notify employee
    await notifyEmployeeActivity({
      request,
      status: ApprovalStatus.APPROVED,
    });

    return `Expense APPROVED by ${approvalDecision.approver}
Comments: ${approvalDecision.comments}
${processResult}`;
  } else {
    // Notify employee of rejection
    await notifyEmployeeActivity({
      request,
      status: approvalStatus,
    });

    const reason = approvalDecision ? approvalDecision.comments : 'Unknown reason';
    return `Expense REJECTED: ${reason}`;
  }
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================
import { Connection, Client } from '@temporalio/client';
import { NativeConnection, Worker } from '@temporalio/worker';
import { randomUUID } from 'crypto';

const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '1-basic-human-in-loop-task-queue';

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
        validateExpense,
        notifyApprover,
        processApprovedExpense,
        notifyEmployee,
      },
    });

    console.log(`Worker started on task queue: ${TASK_QUEUE}`);

    // Run worker in background
    const workerPromise = worker.run();

    // Give worker a moment to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Example 1: Auto-Approval (Small Amount)
    console.log('\n=== Example 1: Auto-Approval (Small Amount) ===\n');

    const request1: ExpenseRequest = {
      employee: 'John Doe',
      amount: 75.5,
      category: 'Office Supplies',
      description: 'Pens and notebooks',
    };

    const result1 = await client.workflow.execute(expenseApprovalWorkflow, {
      args: [request1],
      taskQueue: TASK_QUEUE,
      workflowId: `1-basic-human-in-loop-auto-approval-${randomUUID()}`,
    });
    console.log(`Result: ${result1}\n`);

    // Example 2: Manual Approval Required
    console.log('\n=== Example 2: Manual Approval Required ===\n');

    const request2: ExpenseRequest = {
      employee: 'Jane Smith',
      amount: 2500.0,
      category: 'Travel',
      description: 'Conference attendance and hotel',
    };

    // Start workflow (don't wait)
    const handle = await client.workflow.start(expenseApprovalWorkflow, {
      args: [request2],
      taskQueue: TASK_QUEUE,
      workflowId: `1-basic-human-in-loop-manual-approval-${randomUUID()}`,
    });

    console.log(`Expense request submitted for $${request2.amount}`);
    console.log('Waiting for approval...\n');

    // Check status
    await new Promise(resolve => setTimeout(resolve, 1000));
    const status = await handle.query(getStatusQuery);
    console.log(`Current status: ${status}`);

    // Simulate human approver making a decision
    console.log('\n[Simulating manager approval after review...]');
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Manager approves
    await handle.signal(approveSignal, {
      approved: true,
      approver: 'Manager Sarah Johnson',
      comments: 'Conference attendance is valuable for professional development',
    });

    // Wait for workflow completion
    const result2 = await handle.result();
    console.log(`\n${result2}`);

    // Example 3: Manual Rejection
    console.log('\n=== Example 3: Manual Rejection ===\n');

    const request3: ExpenseRequest = {
      employee: 'Bob Wilson',
      amount: 5000.0,
      category: 'Equipment',
      description: 'New gaming setup',
    };

    const handle3 = await client.workflow.start(expenseApprovalWorkflow, {
      args: [request3],
      taskQueue: TASK_QUEUE,
      workflowId: `1-basic-human-in-loop-rejection-${randomUUID()}`,
    });

    console.log(`Expense request submitted for $${request3.amount}`);
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Manager rejects
    await handle3.signal(rejectSignal, {
      approved: false,
      approver: 'Manager Sarah Johnson',
      comments: 'Gaming setup not related to business needs',
    });

    const result3 = await handle3.result();
    console.log(`\n${result3}`);

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
