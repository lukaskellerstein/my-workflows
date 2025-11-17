/**
 * Workflow Definitions - Human in the Loop
 * Demonstrates workflows waiting for human approval via signals
 */
import {
  proxyActivities,
  defineSignal,
  defineQuery,
  setHandler,
  condition,
  log as workflowLog,
} from '@temporalio/workflow';
import type { ExpenseRequest, EmployeeNotification } from './activities.js';

export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  TIMEOUT = 'timeout',
}

export interface ApprovalDecision {
  approved: boolean;
  approver: string;
  comments: string;
}

// Define activity interface
export interface Activities {
  validateExpense(request: ExpenseRequest): Promise<boolean>;
  notifyApprover(request: ExpenseRequest): Promise<string>;
  processApprovedExpense(request: ExpenseRequest): Promise<string>;
  notifyEmployee(notification: EmployeeNotification): Promise<string>;
}

// Proxy activities with timeout configuration
const { validateExpense, notifyApprover, processApprovedExpense, notifyEmployee } =
  proxyActivities<Activities>({
    startToCloseTimeout: '10 seconds',
  });

// Define signals
export const approveSignal = defineSignal<[ApprovalDecision]>('approve');
export const rejectSignal = defineSignal<[ApprovalDecision]>('reject');

// Define queries
export const getStatusQuery = defineQuery<string>('getStatus');
export const getRequestDetailsQuery = defineQuery<ExpenseRequest | null>('getRequestDetails');

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

  // Set up query handlers
  setHandler(getStatusQuery, () => approvalStatus);
  setHandler(getRequestDetailsQuery, () => request);

  workflowLog.info('Expense approval workflow started:', {
    employee: request.employee,
    amount: request.amount,
  });

  // Step 1: Validate expense
  const isValid = await validateExpense(request);

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
    await notifyApprover(request);

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
    const processResult = await processApprovedExpense(request);

    // Notify employee
    await notifyEmployee({
      request,
      status: ApprovalStatus.APPROVED,
    });

    return `Expense APPROVED by ${approvalDecision.approver}
Comments: ${approvalDecision.comments}
${processResult}`;
  } else {
    // Notify employee of rejection
    await notifyEmployee({
      request,
      status: approvalStatus,
    });

    const reason = approvalDecision ? approvalDecision.comments : 'Unknown reason';
    return `Expense REJECTED: ${reason}`;
  }
}
