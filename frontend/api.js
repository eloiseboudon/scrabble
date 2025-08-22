// Self-executing function to avoid polluting global scope
(function () {
    const { protocol, hostname } = window.location;


    const isProduction = hostname === 'app-scrabble.tulip-saas.fr';
    const port = isProduction ? 8001 : 8000;
    const API_BASE = `${protocol}//${hostname}:${port}`;

    console.log('[api] Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
    console.log('[api] hostname:', hostname);
    console.log('[api] API_BASE:', API_BASE);

    // Make it available globally
    window.API_BASE = API_BASE;

    // Export for ES modules if supported
    if (typeof exports !== 'undefined') {
        exports.API_BASE = API_BASE;
    }
})();

