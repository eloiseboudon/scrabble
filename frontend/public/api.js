// api.js as ES6 module
const { protocol, hostname } = window.location;

const isProduction = hostname === 'app-scrabble.tulip-saas.fr';
const port = isProduction ? 8001 : 8000;

let API_BASE;
if (isProduction) {
    API_BASE = `${protocol}//${hostname}:${port}`;
} else {
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        API_BASE = `${protocol}//${hostname}:${port}`;
    } else {
        API_BASE = `http://localhost:8000`;
    }
}

console.log('[api] Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
console.log('[api] hostname:', hostname);
console.log('[api] API_BASE:', API_BASE);

// Make it available globally
window.API_BASE = API_BASE;

// Export as ES6 module
export { API_BASE };
