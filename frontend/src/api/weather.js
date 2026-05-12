import client from './client';

export async function getWeather(city) {
  const { data } = await client.get('/api/weather/', { params: { city } });
  return data;
}
