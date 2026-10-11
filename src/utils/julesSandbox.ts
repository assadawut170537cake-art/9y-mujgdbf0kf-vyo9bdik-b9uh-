/**
 * ฟังก์ชันจำลองการดึงข้อมูลเพื่อทดสอบ Suggested Tasks ของ Jules
 * Input: endpointUrl (string)
 * Output: Promise<object | null>
 */

// TODO(jules): Add resilience and error logging
// Target: src/utils/julesSandbox.ts
// Requirements:
// 1. Wrap the async logic in a robust try-catch block.
// 2. On error, log the error with prefix "[FetchError]" and return null instead of throwing.
// 3. Document parameter and return types explicitly above the function.
// Test: Add a unit test verifying null return on simulated network failure.

export async function fetchSandboxData(endpointUrl: string): Promise<object | null> {
  const response = await fetch(endpointUrl);
  const data = await response.json();
  return data;
}
