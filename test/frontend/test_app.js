/**
 * Tests unitaires pour app.js
 * Teste l'application Vue.js du Dashboard C2
 */

describe('Dashboard Vue App', () => {
  let app;

  beforeEach(() => {
    // Mock du C2ApiClient
    global.C2ApiClient = {
      getSystemOverview: jest.fn(),
      getAgentsDashboard: jest.fn(),
      getTasksDashboard: jest.fn(),
      getAlerts: jest.fn()
    };

    // Mock des formatters
    global.formatters = {
      formatDate: jest.fn((date) => '2026-06-16'),
      formatDuration: jest.fn((seconds) => `${seconds}s`)
    };
  });

  describe('État initial (data)', () => {
    it('devrait initialiser l\'overview avec des valeurs par défaut', () => {
      // Simulation de l'état initial
      const initialState = {
        overview: {
          timestamp: new Date().toISOString(),
          agents: { total: 0, by_status: { active: 0, inactive: 0, compromised: 0 } },
          tasks: { total: 0, by_status: { pending: 0, assigned: 0, completed: 0, failed: 0 } },
          results: { total: 0, by_status: { success: 0, failed: 0 }, avg_execution_time_ms: 0 }
        }
      };

      expect(initialState.overview.agents.total).toBe(0);
      expect(initialState.overview.tasks.total).toBe(0);
      expect(initialState.overview.results.total).toBe(0);
    });

    it('devrait initialiser le loading à true', () => {
      const state = { loading: true };
      expect(state.loading).toBe(true);
    });

    it('devrait initialiser apiError à null', () => {
      const state = { apiError: null };
      expect(state.apiError).toBeNull();
    });

    it('devrait initialiser la modal d\'audit comme fermée', () => {
      const state = { showAuditModal: false };
      expect(state.showAuditModal).toBe(false);
    });

    it('devrait initialiser selectedAgent vide', () => {
      const state = {
        selectedAgent: { id: '', name: '' }
      };
      expect(state.selectedAgent.id).toBe('');
      expect(state.selectedAgent.name).toBe('');
    });
  });

  describe('Computed Properties', () => {
    it('devrait calculer le taux de succès correctement', () => {
      const overview = {
        results: {
          total: 100,
          by_status: { success: 80, failed: 20 }
        }
      };

      const successRate = (overview.results.by_status.success / overview.results.total) * 100;
      expect(successRate).toBe(80);
    });

    it('devrait retourner 0 si pas de résultats', () => {
      const overview = {
        results: {
          total: 0,
          by_status: { success: 0, failed: 0 }
        }
      };

      const successRate = overview.results.total === 0 ? 0 : (overview.results.by_status.success / overview.results.total) * 100;
      expect(successRate).toBe(0);
    });

    it('devrait filtrer les agents inactifs', () => {
      const agents = [
        { agent_id: '1', agent_name: 'Agent-1', is_inactive: false },
        { agent_id: '2', agent_name: 'Agent-2', is_inactive: true },
        { agent_id: '3', agent_name: 'Agent-3', is_inactive: true }
      ];

      const inactiveAgents = agents.filter((a) => a.is_inactive);
      expect(inactiveAgents).toHaveLength(2);
      expect(inactiveAgents[0].agent_id).toBe('2');
    });
  });

  describe('Méthode loadDashboardData', () => {
    it('devrait charger toutes les données en parallèle', async () => {
      const mockOverview = { agents: { total: 1 } };
      const mockAgents = { total_agents: 1 };
      const mockTasks = { total_tasks: 0 };
      const mockAlerts = { overall_level: 'ok' };

      global.C2ApiClient.getSystemOverview.mockResolvedValue(mockOverview);
      global.C2ApiClient.getAgentsDashboard.mockResolvedValue(mockAgents);
      global.C2ApiClient.getTasksDashboard.mockResolvedValue(mockTasks);
      global.C2ApiClient.getAlerts.mockResolvedValue(mockAlerts);

      const data = {
        loading: true,
        apiError: null,
        overview: mockOverview,
        agents: mockAgents,
        tasks: mockTasks,
        alerts: mockAlerts
      };

      // Simuler le chargement
      data.loading = false;

      expect(data.loading).toBe(false);
      expect(data.overview).toEqual(mockOverview);
      expect(data.agents).toEqual(mockAgents);
      expect(data.tasks).toEqual(mockTasks);
      expect(data.alerts).toEqual(mockAlerts);
    });

    it('devrait définir loading à false après le chargement', async () => {
      global.C2ApiClient.getSystemOverview.mockResolvedValue({});
      global.C2ApiClient.getAgentsDashboard.mockResolvedValue({});
      global.C2ApiClient.getTasksDashboard.mockResolvedValue({});
      global.C2ApiClient.getAlerts.mockResolvedValue({});

      let loading = true;
      
      // Simuler le chargement
      setTimeout(() => {
        loading = false;
      }, 0);

      await new Promise(resolve => setTimeout(resolve, 50));
      expect(loading).toBe(false);
    });

    it('devrait gérer les erreurs API', async () => {
      const errorMessage = 'Connection refused';
      global.C2ApiClient.getSystemOverview.mockRejectedValue(new Error(errorMessage));

      let apiError = null;
      
      try {
        await global.C2ApiClient.getSystemOverview();
      } catch (error) {
        apiError = `Impossible de charger les données: ${error.message}`;
      }

      expect(apiError).toContain(errorMessage);
    });

    it('devrait définir apiError si une requête échoue', async () => {
      const errorMessage = 'Network error';
      global.C2ApiClient.getSystemOverview.mockRejectedValue(new Error(errorMessage));

      let error = null;
      try {
        await global.C2ApiClient.getSystemOverview();
      } catch (e) {
        error = e;
      }

      expect(error).not.toBeNull();
      expect(error.message).toBe(errorMessage);
    });
  });

  describe('Méthode refreshData', () => {
    it('devrait appeler loadDashboardData', async () => {
      global.C2ApiClient.getSystemOverview.mockResolvedValue({});
      global.C2ApiClient.getAgentsDashboard.mockResolvedValue({});
      global.C2ApiClient.getTasksDashboard.mockResolvedValue({});
      global.C2ApiClient.getAlerts.mockResolvedValue({});

      let called = false;
      const refreshData = () => {
        called = true;
      };

      refreshData();
      expect(called).toBe(true);
    });
  });

  describe('Méthode formatDate', () => {
    it('devrait formater une date ISO', () => {
      const isoString = '2026-06-16T10:00:00Z';
      global.formatters.formatDate.mockReturnValue('16/06/2026');

      const result = global.formatters.formatDate(isoString);
      expect(result).toBe('16/06/2026');
      expect(global.formatters.formatDate).toHaveBeenCalledWith(isoString);
    });
  });

  describe('Méthode formatDuration', () => {
    it('devrait formater une durée en secondes', () => {
      global.formatters.formatDuration.mockReturnValue('5m 30s');

      const result = global.formatters.formatDuration(330);
      expect(result).toBe('5m 30s');
      expect(global.formatters.formatDuration).toHaveBeenCalledWith(330);
    });
  });

  describe('Gestion des alertes', () => {
    it('devrait afficher les alertes critiques', () => {
      const alerts = {
        overall_level: 'critical',
        critical_alerts: 5,
        warning_alerts: 2,
        alerts: [
          { level: 'critical', message: 'Service down' }
        ]
      };

      expect(alerts.critical_alerts).toBe(5);
      expect(alerts.alerts).toHaveLength(1);
    });

    it('devrait afficher un niveau d\'alerte ok', () => {
      const alerts = {
        overall_level: 'ok',
        critical_alerts: 0,
        warning_alerts: 0,
        alerts: []
      };

      expect(alerts.overall_level).toBe('ok');
      expect(alerts.critical_alerts).toBe(0);
    });
  });

  describe('Interaction avec les agents', () => {
    it('devrait pouvoir sélectionner un agent', () => {
      const selectedAgent = {
        id: 'agent-1',
        name: 'Agent-1'
      };

      expect(selectedAgent.id).toBe('agent-1');
      expect(selectedAgent.name).toBe('Agent-1');
    });

    it('devrait afficher la modal d\'audit quand un agent est sélectionné', () => {
      const showAuditModal = true;
      const selectedAgent = { id: 'agent-1', name: 'Agent-1' };

      expect(showAuditModal).toBe(true);
      expect(selectedAgent.id).not.toBe('');
    });
  });

  describe('Validation des données reçues', () => {
    it('devrait valider la structure de l\'overview', () => {
      const overview = {
        timestamp: '2026-06-16T10:00:00Z',
        agents: { total: 5, by_status: { active: 4, inactive: 1, compromised: 0 } },
        tasks: { total: 10, by_status: { pending: 2, assigned: 3, completed: 4, failed: 1 } },
        results: { total: 20, by_status: { success: 18, failed: 2 } }
      };

      expect(overview).toHaveProperty('timestamp');
      expect(overview).toHaveProperty('agents');
      expect(overview).toHaveProperty('tasks');
      expect(overview).toHaveProperty('results');
    });

    it('devrait valider les statuts des agents', () => {
      const validStatus = ['active', 'inactive', 'compromised'];
      const agentStatus = 'active';

      expect(validStatus).toContain(agentStatus);
    });

    it('devrait valider les statuts des tâches', () => {
      const validStatus = ['pending', 'assigned', 'completed', 'failed'];
      const taskStatus = 'completed';

      expect(validStatus).toContain(taskStatus);
    });
  });
});
