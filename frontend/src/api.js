export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('invoicemind_token');

  let headers = {};
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(options.headers)) {
      options.headers.forEach(([key, value]) => {
        headers[key] = value;
      });
    } else {
      headers = { ...options.headers };
    }
  }

  if (token) {
    const hasAuth = Object.keys(headers).some(
      (key) => key.toLowerCase() === 'authorization'
    );
    if (!hasAuth) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return fetch(url, {
    ...options,
    headers,
  });
}
