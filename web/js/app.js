/**
 * Application Vue.js pour le Dashboard Jadus Audit
 */

const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      // Données du dashboard
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

      // tat de l'application
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
     * Calculer le taux de succès global
     */
    successRate() {
      const total = this.overview.results.total;
      if (total === 0) return 0;
      return (this.overview.results.by_status.success / total) * 100;
    },

    /**
     * Agents inactifs pour affichage séparé
     */
    inactiveAgents() {
      return this.agents.agents.filter((a) => a.is_inactive);
    },
  },

  methods: {
    /**
     * Charger toutes les données du dashboard
     */
    async loadDashboardData() {
      try {
        this.loading = true;
        this.apiError = null;

        // Charger les données en parallèle
        const [overview, agents, tasks, alerts] = await Promise.all([
          JadusApiClient.getSystemOverview(),
          JadusApiClient.getAgentsDashboard(),
          JadusApiClient.getTasksDashboard(),
          JadusApiClient.getAlerts(),
        ]);

        this.overview = overview;
        this.agents = agents;
        this.tasks = tasks;
        this.alerts = alerts;

        this.loading = false;
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        this.apiError = `Impossible de charger les données: ${error.message}`;
        this.loading = false;
      }
    },

    /**
     * Rafraîchir les données du dashboard
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
     * Formater une durée
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
     * Calculer la durée d'inactivité
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

        // Déterminer la commande à envoyer
        const command =
          this.auditCommand === '' ? this.customCommand : this.auditCommand;

        if (!command.trim()) {
          alert('Veuillez sélectionner ou entrer une commande');
          this.auditLoading = false;
          return;
        }

        // Appeler l'API pour créer la tâche
        const result = await JadusApiClient.createTask(
          this.selectedAgent.id,
          command,
          null,
          this.auditPriority
        );

        // Notification de succès
        alert(` Audit lancé avec succès!\n\nID Tâche: ${result.task_id}`);

        this.closeAuditModal();
        this.auditLoading = false;

        // Rafraîchir les données
        setTimeout(() => {
          this.loadDashboardData();
        }, 1000);
      } catch (error) {
        console.error('Erreur lors du lancement de l\'audit:', error);
        alert(`️ Erreur: ${error.message}`);
        this.auditLoading = false;
      }
    },

    /**
     * Réessayer de contacter un agent
     */
    retryAgent(agentId) {
      alert(`Tentative de reconnexion avec l'agent ${agentId}...\n\n(Action: envoyer un beacon de test)`);
      // Ici on pourrait ajouter une logique pour envoyer un signal de reconnexion
    },

    /**
     * Initialiser l'auto-rafraîchissement
     */
    startAutoRefresh() {
      // Rafraîchir toutes les 30 secondes
      this.autoRefreshInterval = setInterval(() => {
        this.loadDashboardData();
      }, 30000);
    },

    /**
     * Arrêter l'auto-rafraîchissement
     */
    stopAutoRefresh() {
      if (this.autoRefreshInterval) {
        clearInterval(this.autoRefreshInterval);
      }
    },
  },

  mounted() {
    console.log('Dashboard Jadus Audit - Application montée');

    // Charger les données
    this.loadDashboardData();

    // Démarrer l'auto-rafraîchissement
    this.startAutoRefresh();

    // Nettoyer lors du démontage
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

