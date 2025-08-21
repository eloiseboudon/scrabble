// Self-executing function to avoid polluting global scope
(function() {
  const { protocol, hostname } = window.location;
  
  // Configuration for production
  const isProduction = hostname === 'app-scrabble.tulip-saas.fr';
  const API_BASE = isProduction
      ? 'http://app-scrabble.tulip-saas.fr:8001'
      : `${protocol}//${hostname}:8000`;

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

