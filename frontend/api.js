const { protocol, hostname } = window.location;
const defaultPort = hostname === 'localhost' ? '8000' : '8001';
export const API_BASE =
    import.meta.env.VITE_API_BASE || `${protocol}//${hostname}:${defaultPort}`;