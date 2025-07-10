// Backend API service
import { apiClient, BASE_URL, ApiResponse, createSSEConnection, SSECallbacks } from './client';
import { AgentSSEEvent } from '../types/event';
import { CreateSessionResponse, GetSessionResponse, ShellViewResponse, FileViewResponse, ListSessionResponse, ShareSessionResponse, GetSharedSessionResponse } from '../types/response';
import type { FileInfo } from './file';

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

export const getVNCUrl = (sessionId: string): string => {
  // Convert http to ws, https to wss
  const wsBaseUrl = BASE_URL.replace(/^http/, 'ws');
  return `${wsBaseUrl}/sessions/${sessionId}/vnc`;
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
export async function viewShellSession(sessionId: string, shellSessionId: string, callbacks?: SSECallbacks<ShellViewResponse>): Promise<() => void> {
  return createSSEConnection<ShellViewResponse>(
    `/sessions/${sessionId}/shell`,
    {
      method: 'POST',
      body: { session_id: shellSessionId }
    },
    callbacks
  );
}

/**
 * View file content
 * @param sessionId Session ID
 * @param file File path
 * @returns File content
 */
export async function viewFile(sessionId: string, file: string, callbacks?: SSECallbacks<FileViewResponse>): Promise<() => void> {
  return createSSEConnection<FileViewResponse>(
    `/sessions/${sessionId}/file`,
    {
      method: 'POST',
      body: { file }
    },
    callbacks
  );
}

export async function getSessionFiles(sessionId: string): Promise<FileInfo[]> {
  const response = await apiClient.get<ApiResponse<FileInfo[]>>(`/sessions/${sessionId}/files`);
  return response.data.data;
}

/**
 * Share Session
 * @param sessionId Session ID
 * @returns ShareSessionResponse
 */
export async function shareSession(sessionId: string): Promise<ShareSessionResponse> {
  const response = await apiClient.post<ApiResponse<ShareSessionResponse>>(`/sessions/${sessionId}/share`);
  return response.data.data;
}

/**
 * Cancel Share Session
 * @param sessionId Session ID
 */
export async function cancelShareSession(sessionId: string): Promise<void> {
  await apiClient.delete<ApiResponse<void>>(`/sessions/${sessionId}/share`);
}

/**
 * Get Shared Session
 * @param shareId Share ID
 * @param shareToken Share Token
 * @returns GetSharedSessionResponse
 */
export async function getSharedSession(shareId: string, shareToken: string): Promise<GetSharedSessionResponse> {
  const response = await apiClient.get<ApiResponse<GetSharedSessionResponse>>(`/sessions/shared/${shareId}`, {
    headers: {
      'X-Share-Token': shareToken
    }
  });
  return response.data.data;
}