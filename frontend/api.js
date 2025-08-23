// frontend/api.js
// Source de vérité : Vite -> VITE_API_BASE. Fallback '' (same-origin via Nginx/proxy).
export const API_BASE = (import.meta?.env?.VITE_API_BASE ?? '').toString();

// Helpers standards
export async function apiGet(path) {
    const url = (path.startsWith('/') ? path : `/${path}`);
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) {
        let body = null; try { body = await res.json(); } catch { }
        const err = new Error(`HTTP ${res.status}`); err.status = res.status; err.body = body; throw err;
    }
    return res.json();
}

export async function apiPost(path, data) {
    const url = (path.startsWith('/') ? path : `/${path}`);
    const res = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data ?? {}),
    });
    let body = null; try { body = await res.json(); } catch { }
    if (!res.ok) {
        const err = new Error(`HTTP ${res.status}`); err.status = res.status; err.body = body; throw err;
    }
    return body;
}
