// Backend API service
import { apiClient, BASE_URL, ApiResponse, createSSEConnection, SSECallbacks } from './client';
import { AgentSSEEvent } from '../types/event';
import { CreateSessionResponse, GetSessionResponse, ShellViewResponse, FileViewResponse, ListSessionResponse } from '../types/response';
import type { FileInfo } from './file';
import { createVncAccessToken } from './auth';

/**
 * Create Session
 * @returns Session
 */
export async function createSession(): Promise<CreateSessionResponse> {
  const response = await apiClient.put<ApiResponse<CreateSessionResponse>>('/sessions');
  return response.data.data;
}

export async function getSession(sessionId: string): Promise<GetSessionResponse> {
  const response = await apiClient.get<ApiResponse<GetSessionResponse>>(`/sessions/${sessionId}`);
  return response.data.data;
}

export async function getSessions(): Promise<ListSessionResponse> {
  const response = await apiClient.get<ApiResponse<ListSessionResponse>>('/sessions');
  return response.data.data;
}

export async function getSessionsSSE(callbacks?: SSECallbacks<ListSessionResponse>): Promise<() => void> {
  return createSSEConnection<ListSessionResponse>(
    '/sessions',
    {
      method: 'POST'
    },
    callbacks
  );
}

export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete<ApiResponse<void>>(`/sessions/${sessionId}`);
}

export async function stopSession(sessionId: string): Promise<void> {
  await apiClient.post<ApiResponse<void>>(`/sessions/${sessionId}/stop`);
}

/**
 * Get VNC WebSocket URL
 * @param sessionId Session ID
 * @param options Optional configuration
 * @param options.useToken Whether to generate URL with access token (default: false)
 * @param options.expireMinutes Token expiration time in minutes (default: 60, only used when useToken is true)
 * @returns Promise resolving to VNC WebSocket URL string
 * 
 * @example
 * // Traditional URL (requires Authorization header)
 * const url = await getVNCUrl('session123');
 * 
 * @example  
 * // Token-based URL (no Authorization header needed)
 * const url = await getVNCUrl('session123', { useToken: true });
 * const url = await getVNCUrl('session123', { useToken: true, expireMinutes: 120 });
 */
export const getVNCUrl = async (
  sessionId: string, 
  expireMinutes: number = 60
): Promise<string> => {
    const tokenResponse = await createVncAccessToken(sessionId, expireMinutes);
    const wsBaseUrl = BASE_URL.replace(/^http/, 'ws');
    return `${wsBaseUrl}/sessions/${sessionId}/vnc?token=${tokenResponse.access_token}`;
}

/**
 * Chat with Session (using SSE to receive streaming responses)
 * @returns A function to cancel the SSE connection
 */
export const chatWithSession = async (
  sessionId: string, 
  message: string = '',
  eventId?: string,
  attachments?: string[],
  callbacks?: SSECallbacks<AgentSSEEvent['data']>
): Promise<() => void> => {
  return createSSEConnection<AgentSSEEvent['data']>(
    `/sessions/${sessionId}/chat`,
    {
      method: 'POST',
      body: { 
        message, 
        timestamp: Math.floor(Date.now() / 1000), 
        event_id: eventId,
        attachments
      }
    },
    callbacks
  );
};

/**
 * View Shell session output
 * @param sessionId Session ID
 * @param shellSessionId Shell session ID
 * @returns Shell session output content
 */
export async function viewShellSession(sessionId: string, shellSessionId: string): Promise<ShellViewResponse> {
  const response = await apiClient.post<ApiResponse<ShellViewResponse>>(
    `/sessions/${sessionId}/shell`,
    { session_id: shellSessionId }
  );
  return response.data.data;
}

/**
 * View file content
 * @param sessionId Session ID
 * @param file File path
 * @returns File content
 */
export async function viewFile(sessionId: string, file: string): Promise<FileViewResponse> {
  const response = await apiClient.post<ApiResponse<FileViewResponse>>(
    `/sessions/${sessionId}/file`,
    { file }
  );
  return response.data.data;
}

export async function getSessionFiles(sessionId: string): Promise<FileInfo[]> {
  const response = await apiClient.get<ApiResponse<FileInfo[]>>(`/sessions/${sessionId}/files`);
  return response.data.data;
}