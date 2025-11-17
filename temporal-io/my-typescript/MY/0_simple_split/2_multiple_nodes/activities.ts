/**
 * Activity Definitions - Multiple Nodes
 * Activities are tasks that can perform side effects (I/O, API calls, etc.)
 */
import { log as activityLog } from '@temporalio/activity';

/**
 * Activity 1: Validate input
 * Validates that the input value is positive.
 */
export async function validateInput(value: number): Promise<boolean> {
  activityLog.info('Validating input:', { value });
  const isValid = value > 0;
  activityLog.info('Validation result:', { isValid });
  return isValid;
}

/**
 * Activity 2: Transform data
 * Transform data using a mathematical operation.
 */
export async function transformData(value: number): Promise<number> {
  activityLog.info('Transforming data:', { value });
  const result = value * 3 + 10;
  activityLog.info('Transformed result:', { result });
  return result;
}

/**
 * Activity 3: Save result
 * Save the result (simulation).
 */
export async function saveResult(value: number): Promise<string> {
  activityLog.info('Saving result:', { value });
  return `Successfully saved value: ${value}`;
}
