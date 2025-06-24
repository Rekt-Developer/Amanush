import { apiClient } from './client';

export async function uploadAttachment(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  // 这里直接用 apiClient，自动带 baseURL
  const res = await apiClient.post('/attachments/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data.data;
}