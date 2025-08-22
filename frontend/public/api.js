// Self-executing function to avoid polluting global scope
(function () {
    const { protocol, hostname } = window.location;

    // Fixed port detection logic
    const isProduction = hostname === 'app-scrabble.tulip-saas.fr';
    const port = isProduction ? 8001 : 8000;

    // Handle different environments properly
    let API_BASE;
    if (isProduction) {
        // Production: use the correct production port
        API_BASE = `${protocol}//${hostname}:${port}`;
    } else {
        // Development: handle localhost properly
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            API_BASE = `${protocol}//${hostname}:${port}`;
        } else {
            // Fallback for other development scenarios
            API_BASE = `http://localhost:8000`;
        }
    }

    console.log('[api] Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
    console.log('[api] hostname:', hostname);
    console.log('[api] port:', window.location.port);
    console.log('[api] API_BASE:', API_BASE);

    // Diagnostic logging
    console.log('Environment details:', {
        location: window.location.href,
        protocol: window.location.protocol,
        host: window.location.host,
        hostname: window.location.hostname,
        port: window.location.port,
        computed_API_BASE: API_BASE
    });

    // Make it available globally
    window.API_BASE = API_BASE;

    // Export for ES modules if supported
    if (typeof exports !== 'undefined') {
        exports.API_BASE = API_BASE;
    }
})();