const API = import.meta.env.VITE_API_URL || '/api';

export async function accountRequest(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${API}/auth/${path}`, {
      credentials: 'include', signal: controller.signal,
      ...(body !== undefined ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)} : {}),
    });
    const data = response.status === 204 ? null : await response.json();
    if (!response.ok) {
      const error = new Error(typeof data.detail === 'string' ? data.detail : 'Please check your details and try again.');
      error.status = response.status;
      throw error;
    }
    return data;
  } catch (error) {
    if (error.status) throw error;
    throw new Error('Cannot reach the server. Check your connection and try again.');
  } finally { clearTimeout(timer); }
}
