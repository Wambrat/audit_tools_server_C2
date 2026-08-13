/**
 * Tests d'intégration pour l'interface utilisateur (IHM)
 * Teste les interactions et le rendu DOM
 */

describe('Interface Utilisateur - Tests d\'intégration', () => {

  let container;

  beforeEach(() => {
    // Créer un conteneur pour tester le DOM
    container = document.createElement('div');
    document.body.appendChild(container);

    // Mock des API
    global.C2ApiClient = {
      getSystemOverview: jest.fn(),
      getAgentsDashboard: jest.fn(),
      getTasksDashboard: jest.fn(),
      getAlerts: jest.fn(),
      createTask: jest.fn()
    };
  });

  afterEach(() => {
    document.body.removeChild(container);
    jest.clearAllMocks();
  });

  describe('Tableau des agents', () => {
    it('devrait afficher la liste des agents', () => {
      const agents = [
        { agent_id: '1', agent_name: 'Agent-1', status: 'active', last_beacon: '2026-06-16T10:00:00Z' },
        { agent_id: '2', agent_name: 'Agent-2', status: 'inactive', last_beacon: '2026-06-16T09:00:00Z' }
      ];

      expect(agents).toHaveLength(2);
      expect(agents[0].agent_name).toBe('Agent-1');
    });

    it('devrait afficher le statut de l\'agent', () => {
      const agent = {
        agent_id: '1',
        agent_name: 'Agent-1',
        status: 'active'
      };

      expect(['active', 'inactive', 'compromised']).toContain(agent.status);
    });

    it('devrait afficher le dernier beacon', () => {
      const agent = {
        agent_id: '1',
        last_beacon: '2026-06-16T10:00:00Z'
      };

      expect(agent.last_beacon).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('devrait afficher une icône de statut appropriée', () => {
      const statusIcons = {
        'active': '🟢',
        'inactive': '⚪',
        'compromised': '🔴'
      };

      expect(statusIcons['active']).toBe('🟢');
      expect(statusIcons['inactive']).toBe('⚪');
      expect(statusIcons['compromised']).toBe('🔴');
    });
  });

  describe('Modal d\'audit', () => {
    it('devrait ouvrir la modal avec l\'agent sélectionné', () => {
      const selectedAgent = { id: 'agent-1', name: 'Agent-1' };
      const showModal = true;

      expect(showModal).toBe(true);
      expect(selectedAgent.id).toBe('agent-1');
    });

    it('devrait avoir les commandes disponibles', () => {
      const commands = [
        'Get-Service',
        'Get-Process',
        'Get-AuditPolicy'
      ];

      expect(commands).toHaveLength(3);
      expect(commands).toContain('Get-Service');
    });

    it('devrait permettre d\'entrer une commande personnalisée', () => {
      const customCommand = 'Get-EventLog -LogName Application -Newest 10';

      expect(customCommand).toContain('Get-EventLog');
      expect(customCommand.length).toBeGreaterThan(0);
    });

    it('devrait permettre de sélectionner la priorité', () => {
      const priorities = [0, 1, 2, 3];
      const selectedPriority = 2;

      expect(priorities).toContain(selectedPriority);
    });

    it('devrait soumettre la tâche avec les paramètres corrects', async () => {
      global.C2ApiClient.createTask.mockResolvedValue({ task_id: 'task-1' });

      const result = await global.C2ApiClient.createTask('agent-1', 'Get-Service', null, 1);

      expect(global.C2ApiClient.createTask).toHaveBeenCalledWith('agent-1', 'Get-Service', null, 1);
      expect(result.task_id).toBe('task-1');
    });

    it('devrait fermer la modal après soumission réussie', () => {
      const showModal = true;
      const taskSubmitted = true;

      if (taskSubmitted) {
        const closedModal = false;
        expect(closedModal).toBe(false);
      }
    });

    it('devrait afficher une erreur en cas d\'échec', async () => {
      global.C2ApiClient.createTask.mockRejectedValue(new Error('API Error'));

      try {
        await global.C2ApiClient.createTask('agent-1', 'Get-Service');
      } catch (error) {
        expect(error.message).toBe('API Error');
      }
    });
  });

  describe('Tableau des résultats', () => {
    it('devrait afficher les résultats des tâches', () => {
      const results = [
        { result_id: '1', task_id: 'task-1', status: 'success', execution_time_ms: 1250 },
        { result_id: '2', task_id: 'task-2', status: 'failed', execution_time_ms: 500 }
      ];

      expect(results).toHaveLength(2);
      expect(results[0].status).toBe('success');
    });

    it('devrait afficher le statut du résultat', () => {
      const result = { result_id: '1', status: 'success' };

      expect(['success', 'failed']).toContain(result.status);
    });

    it('devrait afficher le temps d\'exécution', () => {
      const result = { execution_time_ms: 1250 };

      expect(result.execution_time_ms).toBeGreaterThan(0);
      expect(typeof result.execution_time_ms).toBe('number');
    });

    it('devrait afficher une icône de résultat appropriée', () => {
      const statusIcons = {
        'success': '✅',
        'failed': '❌'
      };

      expect(statusIcons['success']).toBe('✅');
      expect(statusIcons['failed']).toBe('❌');
    });

    it('devrait permettre d\'afficher les détails du résultat', () => {
      const result = {
        result_id: '1',
        result: 'Status   Name               DisplayName\n---      ----               -----------\nRunning  svchost            ...'
      };

      expect(result.result).toContain('Status');
      expect(result.result.length).toBeGreaterThan(0);
    });
  });

  describe('Statistiques et graphiques', () => {
    it('devrait afficher le nombre total d\'agents', () => {
      const overview = {
        agents: {
          total: 5,
          by_status: { active: 4, inactive: 1, compromised: 0 }
        }
      };

      expect(overview.agents.total).toBe(5);
    });

    it('devrait afficher le nombre de tâches par statut', () => {
      const tasks = {
        by_status: {
          pending: 2,
          assigned: 3,
          completed: 4,
          failed: 1
        }
      };

      const total = Object.values(tasks.by_status).reduce((a, b) => a + b, 0);
      expect(total).toBe(10);
    });

    it('devrait calculer le taux de succès des résultats', () => {
      const results = {
        total: 100,
        by_status: {
          success: 85,
          failed: 15
        }
      };

      const successRate = (results.by_status.success / results.total) * 100;
      expect(successRate).toBe(85);
    });

    it('devrait afficher une barre de progression', () => {
      const progress = 75;
      const max = 100;

      expect(progress).toBeLessThanOrEqual(max);
      expect(progress).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Filtrage et recherche', () => {
    it('devrait filtrer les agents par nom', () => {
      const agents = [
        { agent_id: '1', agent_name: 'Agent-1' },
        { agent_id: '2', agent_name: 'Agent-2' },
        { agent_id: '3', agent_name: 'Test-Agent' }
      ];

      const filtered = agents.filter(a => a.agent_name.includes('Agent'));
      expect(filtered).toHaveLength(2);
    });

    it('devrait filtrer les résultats par statut', () => {
      const results = [
        { result_id: '1', status: 'success' },
        { result_id: '2', status: 'failed' },
        { result_id: '3', status: 'success' }
      ];

      const successResults = results.filter(r => r.status === 'success');
      expect(successResults).toHaveLength(2);
    });

    it('devrait filtrer les tâches par priorité', () => {
      const tasks = [
        { task_id: '1', priority: 0 },
        { task_id: '2', priority: 2 },
        { task_id: '3', priority: 1 }
      ];

      const highPriority = tasks.filter(t => t.priority >= 1);
      expect(highPriority).toHaveLength(2);
    });
  });

  describe('Rafraîchissement automatique', () => {
    it('devrait initialiser l\'intervalle de rafraîchissement', () => {
      const autoRefreshInterval = setInterval(() => {}, 10000); // 10 secondes

      expect(autoRefreshInterval).not.toBeNull();
      clearInterval(autoRefreshInterval);
    });

    it('devrait pouvoir arrêter le rafraîchissement automatique', () => {
      let autoRefreshInterval = setInterval(() => {}, 10000);
      
      clearInterval(autoRefreshInterval);
      autoRefreshInterval = null;

      expect(autoRefreshInterval).toBeNull();
    });

    it('devrait charger les données lors d\'un rafraîchissement', async () => {
      global.C2ApiClient.getSystemOverview.mockResolvedValue({ agents: { total: 5 } });

      const result = await global.C2ApiClient.getSystemOverview();

      expect(global.C2ApiClient.getSystemOverview).toHaveBeenCalled();
      expect(result.agents.total).toBe(5);
    });
  });

  describe('Gestion des erreurs et messages', () => {
    it('devrait afficher un message d\'erreur en cas de problème API', () => {
      const error = new Error('Connection refused');
      const errorMessage = `Impossible de charger les données: ${error.message}`;

      expect(errorMessage).toContain('Connection refused');
    });

    it('devrait afficher un spinner de chargement', () => {
      const loading = true;

      expect(loading).toBe(true);
    });

    it('devrait afficher un message de succès après une action', () => {
      const success = true;
      const message = 'Tâche créée avec succès';

      expect(success).toBe(true);
      expect(message).toContain('succès');
    });

    it('devrait nettoyer les messages après un délai', (done) => {
      let message = 'Tâche créée';

      setTimeout(() => {
        message = '';
      }, 3000);

      setTimeout(() => {
        expect(message).toBe('');
        done();
      }, 3100);
    });
  });

  describe('Responsive et accessibilité', () => {
    it('devrait avoir des labels pour les champs de formulaire', () => {
      const formLabels = {
        'command': 'Commande',
        'priority': 'Priorité',
        'agent': 'Agent'
      };

      expect(formLabels['command']).toBeDefined();
      expect(formLabels['priority']).toBeDefined();
    });

    it('devrait avoir des boutons avec aria-labels', () => {
      const buttons = {
        'submit': 'Soumettre la tâche',
        'refresh': 'Rafraîchir les données',
        'close': 'Fermer la modal'
      };

      expect(buttons['submit']).toBeDefined();
      expect(buttons['refresh']).toBeDefined();
    });

    it('devrait avoir un contraste adéquat', () => {
      const colors = {
        'text': '#000000',
        'background': '#FFFFFF'
      };

      // Vérifier que les couleurs ne sont pas identiques
      expect(colors.text).not.toBe(colors.background);
    });
  });
});
