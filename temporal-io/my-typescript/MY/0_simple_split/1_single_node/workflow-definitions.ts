/**
 * Workflow Definitions
 * Workflows orchestrate activities and contain business logic
 * Must be deterministic - no side effects allowed
 */
import { proxyActivities, log as workflowLog } from '@temporalio/workflow';

// Define activity interface (type-only import is allowed)
export interface Activities {
  processData(inputValue: number): Promise<number>;
}

// Proxy activities with timeout configuration
const { processData } = proxyActivities<Activities>({
  startToCloseTimeout: '10 seconds',
});

/**
 * Simple workflow that executes a single activity
 */
export async function singleNodeWorkflow(inputValue: number): Promise<number> {
  workflowLog.info('Starting workflow with input:', { inputValue });

  // Execute single activity
  const result = await processData(inputValue);

  workflowLog.info('Workflow completed with result:', { result });
  return result;
}
