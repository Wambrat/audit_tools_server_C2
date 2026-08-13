/**
 * Authentication Guard
 * Protège toutes les pages - redirige vers login si pas authentifié
 */

function checkAuthentication() {
  const token = localStorage.getItem('admin_token');
  const exp = localStorage.getItem('admin_token_exp');

  // No token → redirect to login
  if (!token) {
    redirectToLogin();
    return false;
  }

  // Token expired → redirect to login
  if (exp && Date.now() / 1000 > exp) {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_token_exp');
    redirectToLogin();
    return false;
  }

  // Verify token on backend (async)
  verifyTokenOnBackend(token);
  
  return true;
}

/**
 * Verify JWT token validity on backend
 */
async function verifyTokenOnBackend(token) {
  try {
    const response = await fetch('http://localhost:8000/api/monitoring/overview', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    // Token invalid or expired on backend
    if (response.status === 401) {
      console.warn('Token invalid on backend - logging out');
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_token_exp');
      redirectToLogin();
      return false;
    }

    if (!response.ok) {
      console.error(`Backend verification failed: ${response.status}`);
      return false;
    }

    // Token is valid
    return true;

  } catch (error) {
    // Network error - allow access but log warning
    console.warn('Could not verify token on backend (network error):', error);
    // Don't redirect on network errors - user might be offline
    return true;
  }
}

function redirectToLogin() {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  
  // Don't save redirect for pages that redirect themselves
  if (currentPage !== 'admin-login.html' && currentPage !== 'index.html') {
    localStorage.setItem('redirect_after_login', currentPage);
  }
  
  // Show loading message if body exists
  if (document.body) {
    document.body.innerHTML = `
      <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: system-ui, -apple-system, sans-serif;
      ">
        <div style="text-align: center; color: white;">
          <div style="
            font-size: 24px;
            margin-bottom: 20px;
          ">🔐</div>
          <p style="font-size: 18px; margin-bottom: 10px;">Redirection vers la connexion...</p>
          <p style="font-size: 14px; opacity: 0.8;">Veuillez attendre</p>
        </div>
      </div>
    `;
  }
  
  window.location.href = 'admin-login.html';
}

function getToken() {
  return localStorage.getItem('admin_token');
}

function getAuthHeaders() {
  return {
    'Authorization': `Bearer ${getToken()}`,
    'Content-Type': 'application/json'
  };
}

/**
 * Logout user
 */
function logout() {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_token_exp');
  localStorage.removeItem('admin_token_remembered');
  localStorage.removeItem('admin_remembered_username');
  window.location.href = 'admin-login.html?logout=true';
}

/**
 * Intercept all fetch calls to handle 401 errors
 * If token becomes invalid, automatically logout
 */
const originalFetch = window.fetch;
window.fetch = function(...args) {
  return originalFetch.apply(this, args).then(response => {
    // Check if response is 401 (Unauthorized)
    if (response.status === 401) {
      console.warn('Unauthorized - token invalid on backend. Logging out...');
      logout();
    }
    return response;
  }).catch(error => {
    // Network error - just throw it
    throw error;
  });
};

// Check auth on page load (unless on login page)
if (!window.location.pathname.includes('admin-login.html')) {
  checkAuthentication();
  
  // Also verify on backend asynchronously
  const token = localStorage.getItem('admin_token');
  if (token) {
    verifyTokenOnBackend(token);
  }
}
