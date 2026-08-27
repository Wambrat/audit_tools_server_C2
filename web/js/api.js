/**
 * Client API pour communiquer avec le serveur Jadus Audit (FastAPI)
 */

const API_BASE_URL = '/api';

class JadusApiClient {
  /**
   * Récupérer l'aperçu du système
   */
  static async getSystemOverview() {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/overview`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getSystemOverview:', error);
      throw error;
    }
  }

  /**
   * Récupérer le dashboard des agents
   */
  static async getAgentsDashboard() {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/agents`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getAgentsDashboard:', error);
      throw error;
    }
  }

  /**
   * Récupérer le dashboard des tâches
   */
  static async getTasksDashboard() {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/tasks`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getTasksDashboard:', error);
      throw error;
    }
  }

  /**
   * Récupérer le dashboard des résultats
   */
  static async getResultsDashboard() {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/results`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getResultsDashboard:', error);
      throw error;
    }
  }

  /**
   * Récupérer les alertes du système
   */
  static async getAlerts() {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/alerts`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getAlerts:', error);
      throw error;
    }
  }

  /**
   * Récupérer la liste de tous les agents
   */
  static async getAgents() {
    try {
      const response = await fetch(`${API_BASE_URL}/agents`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getAgents:', error);
      throw error;
    }
  }

  /**
   * Créer une nouvelle tâche pour un agent
   * @param {string} agentId - ID de l'agent
   * @param {string} command - Commande à exécuter
   * @param {object} parameters - Paramètres optionnels
   * @param {number} priority - Priorité (par défaut 0)
   */
  static async createTask(agentId, command, parameters = null, priority = 0) {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${agentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command,
          parameters,
          priority,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur createTask:', error);
      throw error;
    }
  }

  /**
   * Récupérer les résultats d'un agent
   */
  static async getAgentResults(agentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/results/${agentId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getAgentResults:', error);
      throw error;
    }
  }

  /**
   * Récupérer les tâches d'un agent
   */
  static async getAgentTasks(agentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${agentId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getAgentTasks:', error);
      throw error;
    }
  }

  /**
   * Récupérer les stats de beacon d'un agent
   */
  static async getBeaconStats(agentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/beacon-stats/${agentId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getBeaconStats:', error);
      throw error;
    }
  }

  /**
   * Récupérer l'historique des beacons d'un agent
   */
  static async getBeaconHistory(agentId, limit = 50) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/beacon-history/${agentId}?limit=${limit}`
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Erreur getBeaconHistory:', error);
      throw error;
    }
  }
}

/**
 * Utilitaires pour formater les données
 */
const formatters = {
  /**
   * Formater une date ISO en format lisible
   */
  formatDate(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString('fr-FR');
  },

  /**
   * Formater une durée en secondes
   */
  formatDuration(seconds) {
    if (!seconds) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  },

  /**
   * Formater un pourcentage
   */
  formatPercent(value, decimals = 1) {
    return `${value.toFixed(decimals)}%`;
  },

  /**
   * Obtenir une classe CSS pour le statut d'un agent
   */
  getStatusClass(status) {
    const mapping = {
      'active': 'status-active',
      'inactive': 'status-inactive',
      'compromised': 'status-compromised',
      'online': 'status-active',
      'offline': 'status-inactive',
    };
    return mapping[status] || 'status-unknown';
  },

  /**
   * Obtenir une classe CSS pour un niveau d'alerte
   */
  getAlertLevelClass(level) {
    const mapping = {
      'ok': 'alert-ok',
      'warning': 'alert-warning',
      'critical': 'alert-critical',
    };
    return mapping[level] || 'alert-unknown';
  },
};

