/**
 * scans.js — API calls for plant scan operations.
 *
 * Backend endpoints:
 *   POST   /api/scans/           Upload image → triggers ML diagnosis → returns full scan result
 *   GET    /api/scans/           Returns list of all scans for the authenticated user
 *   GET    /api/scans/:id/       Returns full detail for a single scan (used when opening from history)
 *   DELETE /api/scans/:id/       Permanently deletes a scan and its image
 *   POST   /api/scans/:id/retry/ Re-runs the ML analysis on an existing scan image
 *
 * All endpoints require a valid Bearer token (attached automatically by client.js).
 */

import client from './client';

/**
 * Upload a plant image for AI diagnosis.
 * Sends as multipart/form-data — do NOT set Content-Type manually,
 * axios will set the correct boundary automatically.
 */
export async function analyzePlant(imageFile, city = '') {
  const form = new FormData();
  form.append('image', imageFile);
  if (city.trim()) form.append('city', city.trim());
  const { data } = await client.post('/api/scans/', form);
  return data;
}

/** Fetch the scan history list for the current user. */
export async function getScanHistory() {
  const { data } = await client.get('/api/scans/');
  return data;
}

/**
 * Fetch full scan details by ID.
 * Used when navigating from the History page to Results,
 * since the history list only includes summary fields.
 */
export async function getScanDetail(id) {
  const { data } = await client.get(`/api/scans/${id}/`);
  return data;
}

/** Delete a scan permanently (image + diagnosis). */
export async function deleteScan(id) {
  await client.delete(`/api/scans/${id}/`);
}

/** Re-run the ML analysis on an existing scan's image. */
export async function retryScan(id) {
  const { data } = await client.post(`/api/scans/${id}/retry/`);
  return data;
}

export async function getScanImageBlob(imageUrl) {
  const { data } = await client.get(imageUrl, { responseType: 'blob' });
  return data;
}

export async function downloadScanReport(id) {
  const { data } = await client.get(`/api/scans/${id}/report/`, { responseType: 'blob' });
  const url = URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.download = `greenlens-scan-${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
