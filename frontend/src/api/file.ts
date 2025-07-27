// File API service
import { apiClient, ApiResponse } from './client';
import { createFileAccessToken } from './auth';

/**
 * File info type
 */
export interface FileInfo {
  file_id: string;
  filename: string;
  content_type?: string;
  size: number;
  upload_date: string;
  metadata?: Record<string, any>;
}

/**
 * Upload file
 * @param file File to upload
 * @param metadata Optional metadata
 * @returns Upload result
 */
export async function uploadFile(file: File, metadata?: Record<string, any>): Promise<FileInfo> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (metadata) {
    formData.append('metadata', JSON.stringify(metadata));
  }

  const response = await apiClient.post<ApiResponse<FileInfo>>('/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data.data;
}

/**
 * Download file
 * @param fileId File ID
 * @returns File download result
 */
export async function downloadFile(fileId: string): Promise<Blob> {
  const response = await apiClient.get(`/files/${fileId}`, {
    responseType: 'blob',
  });
  
  return response.data;
}

/**
 * Delete file
 * @param fileId File ID
 * @returns Success status
 */
export async function deleteFile(fileId: string): Promise<boolean> {
  try {
    await apiClient.delete<ApiResponse<void>>(`/files/${fileId}`);
    return true;
  } catch (error) {
    console.error('Failed to delete file:', error);
    return false;
  }
}

/**
 * Get file information
 * @param fileId File ID
 * @returns File information or null if not found
 */
export async function getFileInfo(fileId: string): Promise<FileInfo | null> {
  try {
    const response = await apiClient.get<ApiResponse<FileInfo>>(`/files/${fileId}`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to get file info:', error);
    return null;
  }
}

/**
 * Get file download URL
 * @param fileId File ID
 * @param options Optional configuration
 * @param options.useToken Whether to generate URL with access token (default: false)
 * @param options.expireMinutes Token expiration time in minutes (default: 60, only used when useToken is true)
 * @returns Promise resolving to download URL string
 * 
 * @example
 * // Traditional URL (requires Authorization header)
 * const url = await getFileDownloadUrl('file123');
 * 
 * @example  
 * // Token-based URL (no Authorization header needed)
 * const url = await getFileDownloadUrl('file123', { useToken: true });
 * const url = await getFileDownloadUrl('file123', { useToken: true, expireMinutes: 120 });
 */
export async function getFileDownloadUrl(
  fileId: string,
  expireMinutes: number = 60
): Promise<string> {
  // Return URL with access token
  const tokenResponse = await createFileAccessToken(fileId, expireMinutes);
  return `${apiClient.defaults.baseURL}/files/${fileId}?token=${tokenResponse.access_token}`;
}
