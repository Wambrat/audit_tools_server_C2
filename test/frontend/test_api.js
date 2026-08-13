/**
 * Tests unitaires pour api.js
 * Teste le client API C2 et les appels aux endpoints
 */

describe('C2ApiClient', () => {
  
  // Mock de fetch
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('getSystemOverview', () => {
    it('devrait retourner l\'aperçu du système', async () => {
      const mockData = {
        timestamp: '2026-06-16T10:00:00Z',
        agents: { total: 5, by_status: { active: 4, inactive: 1, compromised: 0 } },
        tasks: { total: 10, by_status: { pending: 2, assigned: 3, completed: 4, failed: 1 } },
        results: { total: 20, by_status: { success: 18, failed: 2 } }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.getSystemOverview();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/monitoring/overview');
    });

    it('devrait lever une erreur en cas de réponse non-OK', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(C2ApiClient.getSystemOverview()).rejects.toThrow();
    });

    it('devrait gérer les erreurs réseau', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(C2ApiClient.getSystemOverview()).rejects.toThrow('Network error');
    });
  });

  describe('getAgentsDashboard', () => {
    it('devrait retourner le dashboard des agents', async () => {
      const mockData = {
        total_agents: 3,
        agents: [
          { agent_id: '1', agent_name: 'Agent-1', status: 'active' },
          { agent_id: '2', agent_name: 'Agent-2', status: 'inactive' }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.getAgentsDashboard();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/monitoring/agents');
    });
  });

  describe('getTasksDashboard', () => {
    it('devrait retourner le dashboard des tâches', async () => {
      const mockData = {
        total_tasks: 10,
        by_status: { pending: 2, assigned: 3, completed: 4, failed: 1 }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.getTasksDashboard();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/monitoring/tasks');
    });
  });

  describe('getResultsDashboard', () => {
    it('devrait retourner le dashboard des résultats', async () => {
      const mockData = {
        total_results: 20,
        by_status: { success: 18, failed: 2 },
        avg_execution_time_ms: 1500
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.getResultsDashboard();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/monitoring/results');
    });
  });

  describe('getAlerts', () => {
    it('devrait retourner les alertes système', async () => {
      const mockData = {
        overall_level: 'warning',
        critical_alerts: 1,
        warning_alerts: 3,
        alerts: []
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.getAlerts();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/monitoring/alerts');
    });
  });

  describe('getAgents', () => {
    it('devrait retourner la liste des agents', async () => {
      const mockData = [
        { agent_id: '1', agent_name: 'Agent-1' },
        { agent_id: '2', agent_name: 'Agent-2' }
      ];

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.getAgents();

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/agents');
    });
  });

  describe('createTask', () => {
    it('devrait créer une tâche avec succès', async () => {
      const mockData = { task_id: 'task-1', status: 'pending' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const result = await C2ApiClient.createTask('agent-1', 'Get-Service');

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/tasks/agent-1',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    it('devrait inclure les paramètres dans la tâche', async () => {
      const mockData = { task_id: 'task-1', status: 'pending' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      await C2ApiClient.createTask('agent-1', 'Get-Service', { name: 'svchost' }, 1);

      const callArgs = global.fetch.mock.calls[0][1];
      const body = JSON.parse(callArgs.body);

      expect(body.command).toBe('Get-Service');
      expect(body.parameters).toEqual({ name: 'svchost' });
      expect(body.priority).toBe(1);
    });
  });

  describe('Gestion d\'erreurs', () => {
    it('devrait logger les erreurs en console', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      global.fetch.mockRejectedValueOnce(new Error('API Error'));

      try {
        await C2ApiClient.getSystemOverview();
      } catch (e) {
        // Erreur attendue
      }

      expect(consoleSpy).toHaveBeenCalledWith('Erreur getSystemOverview:', expect.any(Error));
      consoleSpy.mockRestore();
    });

    it('devrait gérer les réponses HTTP 404', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      await expect(C2ApiClient.getAgents()).rejects.toThrow('HTTP 404');
    });

    it('devrait gérer les réponses HTTP 500', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(C2ApiClient.getSystemOverview()).rejects.toThrow('HTTP 500');
    });
  });
});
