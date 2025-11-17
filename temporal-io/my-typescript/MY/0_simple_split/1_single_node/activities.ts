/**
 * Activity Definitions
 * Activities are tasks that can perform side effects (I/O, API calls, etc.)
 */
import { log as activityLog } from '@temporalio/activity';

/**
 * Single activity that processes data
 */
export async function processData(inputValue: number): Promise<number> {
  activityLog.info('Processing data:', { inputValue });
  const result = inputValue * 2;
  activityLog.info('Result:', { result });
  return result;
}
