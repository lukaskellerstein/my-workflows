/**
 * Workflow Definitions - Multiple Nodes
 * Workflows orchestrate activities and contain business logic
 * Must be deterministic - no side effects allowed
 *
 * Demonstrates a workflow with multiple activities executed sequentially:
 * 1. Validate input
 * 2. Transform data
 * 3. Save result
 */
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface (type-only import is allowed)
export interface Activities {
  validateInput(value: number): Promise<boolean>;
  transformData(value: number): Promise<number>;
  saveResult(value: number): Promise<string>;
}

// Proxy activities with timeout configuration
const { validateInput, transformData, saveResult } = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Workflow that executes multiple activities in sequence
 */
export async function multipleNodesWorkflow(inputValue: number): Promise<string> {
  workflowLog.info('Starting workflow with input:', { inputValue });

  // Node 1: Validate input
  const isValid = await validateInput(inputValue);

  if (!isValid) {
    workflowLog.warn('Input validation failed');
    return 'Input validation failed';
  }

  // Node 2: Transform data
  const transformed = await transformData(inputValue);

  // Node 3: Save result
  const saveMessage = await saveResult(transformed);

  workflowLog.info('Workflow completed:', { saveMessage });
  return saveMessage;
}
