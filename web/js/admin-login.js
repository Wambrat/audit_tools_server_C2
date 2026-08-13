/**
 * Admin Login Vue Application
 * Handles admin authentication and JWT token management
 */

const { createApp } = Vue;

createApp({
  data() {
    return {
      form: {
        username: '',
        password: '',
        rememberMe: false
      },
      errors: {
        username: '',
        password: '',
        general: ''
      },
      successMessage: '',
      isLoading: false,
      apiBaseUrl: 'http://localhost:8000/api'
    }
  },

  mounted() {
    // Check if already logged in
    if (this.getToken()) {
      window.location.href = 'admin.html';
      return;
    }

    // Restore remembered username if exists
    const rememberedUsername = localStorage.getItem('admin_remembered_username');
    if (rememberedUsername) {
      this.form.username = rememberedUsername;
      this.form.rememberMe = true;
    }

    // Check for logout message
    if (new URLSearchParams(window.location.search).get('logout') === 'true') {
      this.showMessage('Déconnexion réussie', 'success');
    }
  },

  methods: {
    /**
     * Handle login form submission
     */
    async handleLogin() {
      // Clear previous errors
      this.errors = { username: '', password: '', general: '' };
      this.successMessage = '';

      // Validate inputs
      if (!this.form.username.trim()) {
        this.errors.username = 'Le nom d\'utilisateur est requis';
        return;
      }

      if (!this.form.password) {
        this.errors.password = 'Le mot de passe est requis';
        return;
      }

      if (this.form.username.length < 2) {
        this.errors.username = 'Le nom d\'utilisateur doit contenir au moins 2 caractères';
        return;
      }

      if (this.form.password.length < 3) {
        this.errors.password = 'Le mot de passe doit contenir au moins 3 caractères';
        return;
      }

      // Attempt login
      this.isLoading = true;

      try {
        const response = await fetch(`${this.apiBaseUrl}/admin/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: this.form.username,
            password: this.form.password
          })
        });

        const data = await response.json();

        if (!response.ok) {
          // Handle specific errors
          if (response.status === 401) {
            this.errors.general = 'Nom d\'utilisateur ou mot de passe incorrect';
          } else if (response.status === 429) {
            this.errors.general = 'Trop de tentatives de connexion. Veuillez réessayer dans quelques minutes.';
          } else if (data.detail) {
            this.errors.general = data.detail;
          } else {
            this.errors.general = 'Erreur de connexion. Veuillez réessayer.';
          }
          this.isLoading = false;
          return;
        }

        // Store token
        const token = data.access_token;
        this.storeToken(token, this.form.rememberMe);

        // Remember username if checked
        if (this.form.rememberMe) {
          localStorage.setItem('admin_remembered_username', this.form.username);
        } else {
          localStorage.removeItem('admin_remembered_username');
        }

        // Show success message
        this.successMessage = 'Connexion réussie! Redirection en cours...';

        // Redirect after brief delay
        setTimeout(() => {
          const redirectPage = localStorage.getItem('redirect_after_login') || 'admin.html';
          localStorage.removeItem('redirect_after_login');
          window.location.href = redirectPage === 'admin-login.html' ? 'admin.html' : redirectPage;
        }, 1000);

      } catch (error) {
        console.error('Login error:', error);
        this.errors.general = 'Erreur de communication avec le serveur. Veuillez vérifier que le serveur est démarré.';
        this.isLoading = false;
      }
    },

    /**
     * Clear the login form
     */
    clearForm() {
      this.form.password = '';
      this.errors = { username: '', password: '', general: '' };
      this.successMessage = '';
    },

    /**
     * Store JWT token in localStorage
     */
    storeToken(token, rememberMe) {
      localStorage.setItem('admin_token', token);
      if (rememberMe) {
        localStorage.setItem('admin_token_remembered', 'true');
      }
      // Decode token to get expiration time
      const payload = this.parseJwt(token);
      localStorage.setItem('admin_token_exp', payload.exp);
    },

    /**
     * Retrieve JWT token from localStorage
     */
    getToken() {
      return localStorage.getItem('admin_token');
    },

    /**
     * Parse JWT token to get payload
     */
    parseJwt(token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
      } catch (error) {
        console.error('Error parsing JWT:', error);
        return null;
      }
    },

    /**
     * Show status message
     */
    showMessage(message, type) {
      if (type === 'success') {
        this.successMessage = message;
      } else if (type === 'error') {
        this.errors.general = message;
      }
    },

    /**
     * Contact admin - shows how to contact
     */
    contactAdmin() {
      alert('Veuillez contacter votre administrateur système pour obtenir l\'accès.\n\nEmail: admin@example.com\nTéléphone: +33 1 XX XX XX XX');
    }
  }
}).mount('#app');
