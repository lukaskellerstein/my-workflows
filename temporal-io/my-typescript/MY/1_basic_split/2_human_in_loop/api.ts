/**
 * Express Workflow Starter - Human in the Loop
 * REST API to start expense approval workflows and send signals
 */
import express, { Request, Response } from 'express';
import { Connection, Client } from '@temporalio/client';
import {
  expenseApprovalWorkflow,
  approveSignal,
  rejectSignal,
  getStatusQuery,
  getRequestDetailsQuery,
  type ApprovalDecision,
} from './workflow-definitions.js';
import type { ExpenseRequest } from './activities.js';

// Configuration
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '1-basic-human-in-loop-task-queue';
const PORT = 8003;

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
interface ExpenseRequestBody extends ExpenseRequest {
  workflow_id?: string;
}

interface ApprovalDecisionBody {
  approver: string;
  comments: string;
}

interface WorkflowResponse {
  workflow_id: string;
  message: string;
  status: string;
}

interface WorkflowStatusResponse {
  workflow_id: string;
  status: string;
  request?: ExpenseRequest;
  message: string;
}

/**
 * Root endpoint with API information
 */
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Human in the Loop API',
    version: '1.0.0',
    description: 'Expense approval workflows with human decision-making via signals',
    endpoints: {
      start_expense: '/expense/start',
      approve: '/expense/:workflow_id/approve',
      reject: '/expense/:workflow_id/reject',
      status: '/expense/:workflow_id/status',
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
 * Start a new expense approval workflow
 *
 * Small amounts (≤$100) are auto-approved.
 * Larger amounts require manual approval via signals.
 */
app.post('/expense/start', async (req: Request, res: Response) => {
  try {
    const request = req.body as ExpenseRequestBody;

    // Validate request
    if (!request.employee || !request.amount || !request.category || !request.description) {
      res.status(400).json({
        error: 'Missing required fields: employee, amount, category, and description are required',
      });
      return;
    }

    if (request.amount <= 0) {
      res.status(400).json({
        error: 'Amount must be a positive number',
      });
      return;
    }

    // Generate workflow ID if not provided
    const workflowId =
      request.workflow_id ||
      `expense-${request.employee.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}`;

    // Create expense request object
    const expenseRequest: ExpenseRequest = {
      employee: request.employee,
      amount: request.amount,
      category: request.category,
      description: request.description,
    };

    // For small amounts, execute and wait. For large amounts, just start
    if (request.amount <= 100) {
      // Auto-approval - wait for completion
      const result = await temporalClient.workflow.execute(expenseApprovalWorkflow, {
        args: [expenseRequest],
        taskQueue: TASK_QUEUE,
        workflowId,
      });

      const response: WorkflowResponse = {
        workflow_id: workflowId,
        message: result,
        status: 'completed',
      };
      res.json(response);
    } else {
      // Manual approval needed - start and return immediately
      await temporalClient.workflow.start(expenseApprovalWorkflow, {
        args: [expenseRequest],
        taskQueue: TASK_QUEUE,
        workflowId,
      });

      const response: WorkflowResponse = {
        workflow_id: workflowId,
        message: 'Expense submitted for approval. Use the approve/reject endpoints to make a decision.',
        status: 'pending',
      };
      res.json(response);
    }
  } catch (error) {
    console.error('Workflow execution error:', error);
    res.status(500).json({
      error: 'Workflow execution failed',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Approve an expense
 */
app.post('/expense/:workflow_id/approve', async (req: Request, res: Response) => {
  try {
    const workflowId = req.params.workflow_id;
    const body = req.body as ApprovalDecisionBody;

    if (!body.approver || !body.comments) {
      res.status(400).json({
        error: 'Missing required fields: approver and comments are required',
      });
      return;
    }

    // Get workflow handle
    const handle = temporalClient.workflow.getHandle(workflowId);

    // Send approval signal
    const decision: ApprovalDecision = {
      approved: true,
      approver: body.approver,
      comments: body.comments,
    };
    await handle.signal(approveSignal, decision);

    const response: WorkflowResponse = {
      workflow_id: workflowId,
      message: `Expense approved by ${body.approver}`,
      status: 'approved',
    };
    res.json(response);
  } catch (error) {
    console.error('Approval error:', error);
    res.status(500).json({
      error: 'Failed to approve expense',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Reject an expense
 */
app.post('/expense/:workflow_id/reject', async (req: Request, res: Response) => {
  try {
    const workflowId = req.params.workflow_id;
    const body = req.body as ApprovalDecisionBody;

    if (!body.approver || !body.comments) {
      res.status(400).json({
        error: 'Missing required fields: approver and comments are required',
      });
      return;
    }

    // Get workflow handle
    const handle = temporalClient.workflow.getHandle(workflowId);

    // Send rejection signal
    const decision: ApprovalDecision = {
      approved: false,
      approver: body.approver,
      comments: body.comments,
    };
    await handle.signal(rejectSignal, decision);

    const response: WorkflowResponse = {
      workflow_id: workflowId,
      message: `Expense rejected by ${body.approver}`,
      status: 'rejected',
    };
    res.json(response);
  } catch (error) {
    console.error('Rejection error:', error);
    res.status(500).json({
      error: 'Failed to reject expense',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Get workflow status
 */
app.get('/expense/:workflow_id/status', async (req: Request, res: Response) => {
  try {
    const workflowId = req.params.workflow_id;

    // Get workflow handle
    const handle = temporalClient.workflow.getHandle(workflowId);

    // Query status
    const status = await handle.query(getStatusQuery);
    const requestDetails = await handle.query(getRequestDetailsQuery);

    const response: WorkflowStatusResponse = {
      workflow_id: workflowId,
      status,
      request: requestDetails || undefined,
      message: `Workflow is currently ${status}`,
    };
    res.json(response);
  } catch (error) {
    console.error('Status query error:', error);
    res.status(500).json({
      error: 'Failed to get workflow status',
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
      console.log('');
      console.log('Example requests:');
      console.log('');
      console.log('1. Start expense (auto-approved):');
      console.log(`  curl -X POST http://localhost:${PORT}/expense/start \\`);
      console.log(`    -H "Content-Type: application/json" \\`);
      console.log(`    -d '{"employee": "John Doe", "amount": 75, "category": "Office", "description": "Supplies"}'`);
      console.log('');
      console.log('2. Start expense (needs approval):');
      console.log(`  curl -X POST http://localhost:${PORT}/expense/start \\`);
      console.log(`    -H "Content-Type: application/json" \\`);
      console.log(`    -d '{"employee": "Jane Smith", "amount": 2500, "category": "Travel", "description": "Conference", "workflow_id": "expense-123"}'`);
      console.log('');
      console.log('3. Approve expense:');
      console.log(`  curl -X POST http://localhost:${PORT}/expense/expense-123/approve \\`);
      console.log(`    -H "Content-Type: application/json" \\`);
      console.log(`    -d '{"approver": "Manager Sarah", "comments": "Approved for Q1"}'`);
      console.log('');
      console.log('4. Check status:');
      console.log(`  curl http://localhost:${PORT}/expense/expense-123/status`);
    });
  } catch (error) {
    console.error('Failed to start API server:', error);
    process.exit(1);
  }
}

main();
