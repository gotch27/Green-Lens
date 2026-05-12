import client from './client';

export async function analyzePlant(imageFile) {
  const form = new FormData();
  form.append('image', imageFile);
  const { data } = await client.post('/api/scans/', form);
  return data;
}

export async function getScanHistory() {
  const { data } = await client.get('/api/scans/');
  return data;
}

export async function getScanDetail(id) {
  const { data } = await client.get(`/api/scans/${id}/`);
  return data;
}

export async function deleteScan(id) {
  await client.delete(`/api/scans/${id}/`);
}

export async function retryScan(id) {
  const { data } = await client.post(`/api/scans/${id}/retry/`);
  return data;
}
