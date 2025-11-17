/**
 * Workflow Starter Script - Human in the Loop
 * Script to start expense approval workflows with different scenarios
 */
import { Connection, Client } from '@temporalio/client';
import {
  expenseApprovalWorkflow,
  approveSignal,
  rejectSignal,
  getStatusQuery,
  type ApprovalDecision,
} from './workflow-definitions.js';
import type { ExpenseRequest } from './activities.js';
import { randomUUID } from 'crypto';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '1-basic-human-in-loop-task-queue';

async function main() {
  try {
    // Connect to Temporal server
    const connection = await Connection.connect({ address: TEMPORAL_HOST });
    const client = new Client({ connection });
    console.log(`Connected to Temporal at ${TEMPORAL_HOST}`);

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
    const approval: ApprovalDecision = {
      approved: true,
      approver: 'Manager Sarah Johnson',
      comments: 'Conference attendance is valuable for professional development',
    };
    await handle.signal(approveSignal, approval);

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
    const rejection: ApprovalDecision = {
      approved: false,
      approver: 'Manager Sarah Johnson',
      comments: 'Gaming setup not related to business needs',
    };
    await handle3.signal(rejectSignal, rejection);

    const result3 = await handle3.result();
    console.log(`\n${result3}`);
  } catch (error) {
    console.error('Error executing workflow:', error);
    process.exit(1);
  }
}

main();
