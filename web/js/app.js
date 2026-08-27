/**
 * Application Vue.js pour le Dashboard jadus
 */

const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      // DonnÃ©es du dashboard
      overview: {
        timestamp: new Date().toISOString(),
        agents: {
          total: 0,
          by_status: {
            active: 0,
            inactive: 0,
            compromised: 0,
          },
        },
        tasks: {
          total: 0,
          by_status: {
            pending: 0,
            assigned: 0,
            completed: 0,
            failed: 0,
          },
        },
        results: {
          total: 0,
          by_status: {
            success: 0,
            failed: 0,
          },
          avg_execution_time_ms: 0,
        },
      },

      agents: {
        total_agents: 0,
        agents: [],
      },

      tasks: {
        total_tasks: 0,
        by_status: {
          pending: 0,
          assigned: 0,
          completed: 0,
          failed: 0,
        },
        avg_execution_time_seconds: 0,
        overdue_tasks_count: 0,
        overdue_task_ids: [],
      },

      alerts: {
        timestamp: new Date().toISOString(),
        overall_level: 'ok',
        critical_alerts: 0,
        warning_alerts: 0,
        alerts: [],
      },

      // Ã‰tat de l'application
      loading: true,
      apiError: null,
      autoRefreshInterval: null,

      // Modal d'audit
      showAuditModal: false,
      selectedAgent: {
        id: '',
        name: '',
      },
      auditCommand: '',
      customCommand: '',
      auditPriority: 0,
      auditLoading: false,
    };
  },

  computed: {
    /**
     * Calculer le taux de succÃ¨s global
     */
    successRate() {
      const total = this.overview.results.total;
      if (total === 0) return 0;
      return (this.overview.results.by_status.success / total) * 100;
    },

    /**
     * Agents inactifs pour affichage sÃ©parÃ©
     */
    inactiveAgents() {
      return this.agents.agents.filter((a) => a.is_inactive);
    },
  },

  methods: {
    /**
     * Charger toutes les donnÃ©es du dashboard
     */
    async loadDashboardData() {
      try {
        this.loading = true;
        this.apiError = null;

        // Charger les donnÃ©es en parallÃ¨le
        const [overview, agents, tasks, alerts] = await Promise.all([
          jadusApiClient.getSystemOverview(),
          jadusApiClient.getAgentsDashboard(),
          jadusApiClient.getTasksDashboard(),
          jadusApiClient.getAlerts(),
        ]);

        this.overview = overview;
        this.agents = agents;
        this.tasks = tasks;
        this.alerts = alerts;

        this.loading = false;
      } catch (error) {
        console.error('Erreur lors du chargement des donnÃ©es:', error);
        this.apiError = `Impossible de charger les donnÃ©es: ${error.message}`;
        this.loading = false;
      }
    },

    /**
     * RafraÃ®chir les donnÃ©es du dashboard
     */
    refreshData() {
      this.loadDashboardData();
    },

    /**
     * Formater une date ISO
     */
    formatDate(isoString) {
      return formatters.formatDate(isoString);
    },

    /**
     * Formater une durÃ©e
     */
    formatDuration(seconds) {
      return formatters.formatDuration(seconds);
    },

    /**
     * Formater un pourcentage
     */
    formatPercent(value) {
      return formatters.formatPercent(value);
    },

    /**
     * Obtenir une classe CSS pour le statut
     */
    getStatusClass(status) {
      return formatters.getStatusClass(status);
    },

    /**
     * Calculer la durÃ©e d'inactivitÃ©
     */
    getInactivityDuration(lastBeacon) {
      if (!lastBeacon) return 'Jamais';

      const now = new Date();
      const last = new Date(lastBeacon);
      const diffMs = now - last;
      const diffSeconds = Math.floor(diffMs / 1000);

      if (diffSeconds < 60) {
        return "il y a moins d'une minute";
      }

      const diffMinutes = Math.floor(diffSeconds / 60);
      if (diffMinutes < 60) {
        return `il y a ${diffMinutes} min`;
      }

      const diffHours = Math.floor(diffMinutes / 60);
      return `il y a ${diffHours} h`;
    },

    /**
     * Ouvrir le modal de lancement d'audit
     */
    launchAudit(agentId, agentName) {
      this.selectedAgent = {
        id: agentId,
        name: agentName,
      };
      this.auditCommand = 'Get-AuditPolicy';
      this.customCommand = '';
      this.auditPriority = 0;
      this.showAuditModal = true;
    },

    /**
     * Fermer le modal d'audit
     */
    closeAuditModal() {
      this.showAuditModal = false;
    },

    /**
     * Soumettre l'audit
     */
    async submitAudit() {
      if (this.auditLoading) return;

      try {
        this.auditLoading = true;

        // DÃ©terminer la commande Ã  envoyer
        const command =
          this.auditCommand === '' ? this.customCommand : this.auditCommand;

        if (!command.trim()) {
          alert('Veuillez sÃ©lectionner ou entrer une commande');
          this.auditLoading = false;
          return;
        }

        // Appeler l'API pour crÃ©er la tÃ¢che
        const result = await jadusApiClient.createTask(
          this.selectedAgent.id,
          command,
          null,
          this.auditPriority
        );

        // Notification de succÃ¨s
        alert(`âœ“ Audit lancÃ© avec succÃ¨s!\n\nID TÃ¢che: ${result.task_id}`);

        this.closeAuditModal();
        this.auditLoading = false;

        // RafraÃ®chir les donnÃ©es
        setTimeout(() => {
          this.loadDashboardData();
        }, 1000);
      } catch (error) {
        console.error('Erreur lors du lancement de l\'audit:', error);
        alert(`âš ï¸ Erreur: ${error.message}`);
        this.auditLoading = false;
      }
    },

    /**
     * RÃ©essayer de contacter un agent
     */
    retryAgent(agentId) {
      alert(`Tentative de reconnexion avec l'agent ${agentId}...\n\n(Action: envoyer un beacon de test)`);
      // Ici on pourrait ajouter une logique pour envoyer un signal de reconnexion
    },

    /**
     * Initialiser l'auto-rafraÃ®chissement
     */
    startAutoRefresh() {
      // RafraÃ®chir toutes les 30 secondes
      this.autoRefreshInterval = setInterval(() => {
        this.loadDashboardData();
      }, 30000);
    },

    /**
     * ArrÃªter l'auto-rafraÃ®chissement
     */
    stopAutoRefresh() {
      if (this.autoRefreshInterval) {
        clearInterval(this.autoRefreshInterval);
      }
    },
  },

  mounted() {
    console.log('Dashboard jadus - Application montÃ©e');

    // Charger les donnÃ©es
    this.loadDashboardData();

    // DÃ©marrer l'auto-rafraÃ®chissement
    this.startAutoRefresh();

    // Nettoyer lors du dÃ©montage
    window.addEventListener('beforeunload', () => {
      this.stopAutoRefresh();
    });
  },

  beforeUnmount() {
    this.stopAutoRefresh();
  },
});

// Monter l'application
app.mount('#app');

console.log('Vue.js application initialized');

