// Thin wrapper over the DRF API. Same-origin, so session cookies ride along and the
// only thing to handle explicitly is the CSRF token on writes.

export function csrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

export async function apiGet(path, params = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      // DRF's BaseInFilter reads a repeated param as a comma-joined list.
      if (value.length) url.searchParams.set(key, value.join(','));
    } else if (value !== '' && value != null) {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function apiSend(path, method, body) {
  const response = await fetch(path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken(),
    },
    credentials: 'same-origin',
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.status === 204 ? null : response.json();
}
