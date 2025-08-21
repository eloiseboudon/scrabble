const { protocol, hostname } = window.location;

// Configuration pour la production
const isProduction = hostname === 'app-scrabble.tulip-saas.fr';
const API_BASE = isProduction
    ? 'http://app-scrabble.tulip-saas.fr:8001'
    : `${protocol}//${hostname}:8000`;

console.log('[api] Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
console.log('[api] hostname:', hostname);
console.log('[api] API_BASE:', API_BASE);

// Export nommé pour l'import
export { API_BASE };

