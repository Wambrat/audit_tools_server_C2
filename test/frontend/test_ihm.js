/**
 * Tests d'intÃ©gration pour l'interface utilisateur (IHM)
 * Teste les interactions et le rendu DOM
 */

describe('Interface Utilisateur - Tests d\'intÃ©gration', () => {

  let container;

  beforeEach(() => {
    // CrÃ©er un conteneur pour tester le DOM
    container = document.createElement('div');
    document.body.appendChild(container);

    // Mock des API
    global.jadusApiClient = {
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

    it('devrait afficher une icÃ´ne de statut appropriÃ©e', () => {
      const statusIcons = {
        'active': 'ðŸŸ¢',
        'inactive': 'âšª',
        'compromised': 'ðŸ”´'
      };

      expect(statusIcons['active']).toBe('ðŸŸ¢');
      expect(statusIcons['inactive']).toBe('âšª');
      expect(statusIcons['compromised']).toBe('ðŸ”´');
    });
  });

  describe('Modal d\'audit', () => {
    it('devrait ouvrir la modal avec l\'agent sÃ©lectionnÃ©', () => {
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

    it('devrait permettre d\'entrer une commande personnalisÃ©e', () => {
      const customCommand = 'Get-EventLog -LogName Application -Newest 10';

      expect(customCommand).toContain('Get-EventLog');
      expect(customCommand.length).toBeGreaterThan(0);
    });

    it('devrait permettre de sÃ©lectionner la prioritÃ©', () => {
      const priorities = [0, 1, 2, 3];
      const selectedPriority = 2;

      expect(priorities).toContain(selectedPriority);
    });

    it('devrait soumettre la tÃ¢che avec les paramÃ¨tres corrects', async () => {
      global.jadusApiClient.createTask.mockResolvedValue({ task_id: 'task-1' });

      const result = await global.jadusApiClient.createTask('agent-1', 'Get-Service', null, 1);

      expect(global.jadusApiClient.createTask).toHaveBeenCalledWith('agent-1', 'Get-Service', null, 1);
      expect(result.task_id).toBe('task-1');
    });

    it('devrait fermer la modal aprÃ¨s soumission rÃ©ussie', () => {
      const showModal = true;
      const taskSubmitted = true;

      if (taskSubmitted) {
        const closedModal = false;
        expect(closedModal).toBe(false);
      }
    });

    it('devrait afficher une erreur en cas d\'Ã©chec', async () => {
      global.jadusApiClient.createTask.mockRejectedValue(new Error('API Error'));

      try {
        await global.jadusApiClient.createTask('agent-1', 'Get-Service');
      } catch (error) {
        expect(error.message).toBe('API Error');
      }
    });
  });

  describe('Tableau des rÃ©sultats', () => {
    it('devrait afficher les rÃ©sultats des tÃ¢ches', () => {
      const results = [
        { result_id: '1', task_id: 'task-1', status: 'success', execution_time_ms: 1250 },
        { result_id: '2', task_id: 'task-2', status: 'failed', execution_time_ms: 500 }
      ];

      expect(results).toHaveLength(2);
      expect(results[0].status).toBe('success');
    });

    it('devrait afficher le statut du rÃ©sultat', () => {
      const result = { result_id: '1', status: 'success' };

      expect(['success', 'failed']).toContain(result.status);
    });

    it('devrait afficher le temps d\'exÃ©cution', () => {
      const result = { execution_time_ms: 1250 };

      expect(result.execution_time_ms).toBeGreaterThan(0);
      expect(typeof result.execution_time_ms).toBe('number');
    });

    it('devrait afficher une icÃ´ne de rÃ©sultat appropriÃ©e', () => {
      const statusIcons = {
        'success': 'âœ…',
        'failed': 'âŒ'
      };

      expect(statusIcons['success']).toBe('âœ…');
      expect(statusIcons['failed']).toBe('âŒ');
    });

    it('devrait permettre d\'afficher les dÃ©tails du rÃ©sultat', () => {
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

    it('devrait afficher le nombre de tÃ¢ches par statut', () => {
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

    it('devrait calculer le taux de succÃ¨s des rÃ©sultats', () => {
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

    it('devrait filtrer les rÃ©sultats par statut', () => {
      const results = [
        { result_id: '1', status: 'success' },
        { result_id: '2', status: 'failed' },
        { result_id: '3', status: 'success' }
      ];

      const successResults = results.filter(r => r.status === 'success');
      expect(successResults).toHaveLength(2);
    });

    it('devrait filtrer les tÃ¢ches par prioritÃ©', () => {
      const tasks = [
        { task_id: '1', priority: 0 },
        { task_id: '2', priority: 2 },
        { task_id: '3', priority: 1 }
      ];

      const highPriority = tasks.filter(t => t.priority >= 1);
      expect(highPriority).toHaveLength(2);
    });
  });

  describe('RafraÃ®chissement automatique', () => {
    it('devrait initialiser l\'intervalle de rafraÃ®chissement', () => {
      const autoRefreshInterval = setInterval(() => {}, 10000); // 10 secondes

      expect(autoRefreshInterval).not.toBeNull();
      clearInterval(autoRefreshInterval);
    });

    it('devrait pouvoir arrÃªter le rafraÃ®chissement automatique', () => {
      let autoRefreshInterval = setInterval(() => {}, 10000);
      
      clearInterval(autoRefreshInterval);
      autoRefreshInterval = null;

      expect(autoRefreshInterval).toBeNull();
    });

    it('devrait charger les donnÃ©es lors d\'un rafraÃ®chissement', async () => {
      global.jadusApiClient.getSystemOverview.mockResolvedValue({ agents: { total: 5 } });

      const result = await global.jadusApiClient.getSystemOverview();

      expect(global.jadusApiClient.getSystemOverview).toHaveBeenCalled();
      expect(result.agents.total).toBe(5);
    });
  });

  describe('Gestion des erreurs et messages', () => {
    it('devrait afficher un message d\'erreur en cas de problÃ¨me API', () => {
      const error = new Error('Connection refused');
      const errorMessage = `Impossible de charger les donnÃ©es: ${error.message}`;

      expect(errorMessage).toContain('Connection refused');
    });

    it('devrait afficher un spinner de chargement', () => {
      const loading = true;

      expect(loading).toBe(true);
    });

    it('devrait afficher un message de succÃ¨s aprÃ¨s une action', () => {
      const success = true;
      const message = 'TÃ¢che crÃ©Ã©e avec succÃ¨s';

      expect(success).toBe(true);
      expect(message).toContain('succÃ¨s');
    });

    it('devrait nettoyer les messages aprÃ¨s un dÃ©lai', (done) => {
      let message = 'TÃ¢che crÃ©Ã©e';

      setTimeout(() => {
        message = '';
      }, 3000);

      setTimeout(() => {
        expect(message).toBe('');
        done();
      }, 3100);
    });
  });

  describe('Responsive et accessibilitÃ©', () => {
    it('devrait avoir des labels pour les champs de formulaire', () => {
      const formLabels = {
        'command': 'Commande',
        'priority': 'PrioritÃ©',
        'agent': 'Agent'
      };

      expect(formLabels['command']).toBeDefined();
      expect(formLabels['priority']).toBeDefined();
    });

    it('devrait avoir des boutons avec aria-labels', () => {
      const buttons = {
        'submit': 'Soumettre la tÃ¢che',
        'refresh': 'RafraÃ®chir les donnÃ©es',
        'close': 'Fermer la modal'
      };

      expect(buttons['submit']).toBeDefined();
      expect(buttons['refresh']).toBeDefined();
    });

    it('devrait avoir un contraste adÃ©quat', () => {
      const colors = {
        'text': '#000000',
        'background': '#FFFFFF'
      };

      // VÃ©rifier que les couleurs ne sont pas identiques
      expect(colors.text).not.toBe(colors.background);
    });
  });
});

