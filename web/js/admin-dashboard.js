/**
 * Admin Dashboard Vue Application
 * Manages admin interface with authentication and data display
 */

const { createApp } = Vue;

createApp({
  data() {
    return {
      currentPage: 'overview',
      isLoading: false,
      apiBaseUrl: 'http://localhost:8000/api',
      token: null,
      overview: {
        agents: { total: 0, active: 0 },
        results: { total: 0, success_rate: 0 },
        execution_time_avg_ms: 0
      },
      agentsList: [],
      tasksList: [],
      resultsList: [],
      resultsFilterAgent: '',
      resultsFilterStatus: '',
      alertsList: [],
      alertsFilterLevel: '',
      templatesList: [],
      selectedResultId: null,
      showResultModal: false,
      templateCommandOptions: [
        'Get-Process',
        'Get-Service',
        'Get-AuditPolicy',
        'SystemInfo',
        'Get-LocalUser',
        'Get-LocalGroup',
        'Get-IPConfig',
        'Get-EventLog',
        'Get-NetAdapter',
        'Get-ChildItem',
        'Get-ComputerInfo'
      ],
      powershellCommandList: [],
      showCommandForm: false,
      commandFormMode: 'create',
      commandTableSelection: [],
      newCommand: {
        command_id: '',
        name: '',
        description: '',
        script: '',
        created_by: 'admin'
      },
      auditTemplate: {
        name: '',
        description: '',
        commands: [],
        created_by: 'admin'
      },
      selectedTemplateId: '',
      selectedTemplateForApplication: '',
      templateTableSelection: [],
      auditTemplateSelection: '',
      agentTableSelection: [],
      agentDispatchStats: {},
      showTemplateForm: false,
      templateFormMode: 'create',
      templateBuilderSummary: '',
      templateJsonInput: '',
      templateHistory: [],
      templateSearch: '',
      templateCommandSelection: '',
      newTask: {
        agentId: '',
        command: '',
        priority: 0,
        parametersJson: '{}'
      },
      pageTitle: 'Vue d\'ensemble'
    }
  },

  watch: {
    currentPage(newPage) {
      this.updatePageTitle(newPage);
      this.loadPageData(newPage);
    }
  },

  mounted() {
    // Check authentication
    this.token = localStorage.getItem('admin_token');
    if (!this.token) {
      window.location.href = 'admin-login.html';
      return;
    }

    // Check token expiration
    const exp = localStorage.getItem('admin_token_exp');
    if (exp && Date.now() / 1000 > exp) {
      this.logout();
      return;
    }

    // Load initial data
    this.loadPageData('overview');
  },

  computed: {
    uniqueAgents() {
      const map = new Map();
      for (const result of this.resultsList || []) {
        const id = result.agent_id;
        if (!id || map.has(id)) continue;
        map.set(id, {
          agent_id: id,
          agent_name: result.agent_name || id
        });
      }
      return [...map.values()];
    },

    filteredResults() {
      return (this.resultsList || []).filter(result => {
        const complianceStatus = String(result?.compliance?.status || (result?.status === 'failed' ? 'non_compliant' : 'compliant')).toLowerCase();
        const matchesAgent = !this.resultsFilterAgent || result.agent_id === this.resultsFilterAgent;
        const matchesStatus = !this.resultsFilterStatus || complianceStatus === this.resultsFilterStatus;
        return matchesAgent && matchesStatus;
      });
    },

    filteredAlerts() {
      return (this.alertsList || []).filter(alert => {
        const matchesLevel = !this.alertsFilterLevel || alert.level === this.alertsFilterLevel;
        return matchesLevel;
      });
    },

    resultStats() {
      const total = this.resultsList.length;
      const success = (this.resultsList || []).filter(r => (r?.compliance?.status || 'compliant') === 'compliant').length;
      const partiallyCompliant = (this.resultsList || []).filter(r => (r?.compliance?.status || 'compliant') === 'partially_compliant').length;
      const nonCompliant = (this.resultsList || []).filter(r => (r?.compliance?.status || 'compliant') === 'non_compliant').length;
      const failed = (this.resultsList || []).filter(r => r.status === 'failed').length;
      const avgTime = total
        ? Math.round((this.resultsList.reduce((sum, r) => sum + (Number(r.execution_time_ms) || 0), 0) / total))
        : 0;
      return {
        success,
        partiallyCompliant,
        failed,
        nonCompliant,
        total,
        successRate: total ? Math.round((success / total) * 100) : 0,
        avgTime
      };
    },

    selectedResultData() {
      if (!this.selectedResultId) return null;
      return (this.resultsList || []).find(result => result.result_id === this.selectedResultId) || null;
    },

    alertSummary() {
      const alerts = this.alertsList || [];
      const critical = alerts.filter(alert => (alert.level || '').toLowerCase() === 'critical').length;
      const warning = alerts.filter(alert => (alert.level || '').toLowerCase() === 'warning').length;
      const info = alerts.filter(alert => (alert.level || '').toLowerCase() === 'info').length;
      let overall = 'ok';
      if (critical > 0) overall = 'critical';
      else if (warning > 0 || info > 0) overall = 'warning';
      return { critical, warning, info, overall };
    }
  },

  methods: {
    /**
     * Update page title based on current page
     */
    updatePageTitle(page) {
      const titles = {
        'overview': 'Vue d\'ensemble',
        'agents': 'Gestion des Agents',
        'tasks': 'Gestion des Commandes',
        'templates': 'Modèles d\'Audit',
        'results': 'Résultats d\'Audit',
        'alerts': 'Alertes Système',
        'settings': 'Paramètres'
      };
      this.pageTitle = titles[page] || 'Admin Dashboard';
    },

    /**
     * Load data for the current page
     */
    async loadPageData(page) {
      this.isLoading = true;

      try {
        switch (page) {
          case 'overview':
            await this.loadOverview();
            break;
          case 'agents':
            await this.loadAgents();
            await this.loadAuditTemplates();
            break;
          case 'tasks':
            await this.loadTasks();
            await this.loadPowerShellCommands();
            break;
          case 'templates':
            await this.loadAuditTemplates();
            await this.loadPowerShellCommands();
            this.loadAgents();
            break;
          case 'results':
            await this.loadResults();
            break;
          case 'alerts':
            await this.loadAlerts();
            break;
        }
      } catch (error) {
        console.error(`Error loading ${page}:`, error);
        if (error.message === 'Unauthorized') {
          this.logout();
        }
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Load overview data
     */
    async loadOverview() {
      try {
        const response = await fetch(
          `${this.apiBaseUrl}/monitoring/overview`,
          { headers: this.getAuthHeaders() }
        );

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        this.overview = data;
      } catch (error) {
        console.error('Error loading overview:', error);
        throw error;
      }
    },

    /**
     * Load agents data
     */
    async loadAgents() {
      try {
        const response = await fetch(
          `${this.apiBaseUrl}/monitoring/agents`,
          { headers: this.getAuthHeaders() }
        );

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        this.agentsList = data.agents || [];
      } catch (error) {
        console.error('Error loading agents:', error);
        throw error;
      }
    },

    /**
     * Load tasks data
     */
    async loadTasks() {
      try {
        const response = await fetch(
          `${this.apiBaseUrl}/monitoring/tasks`,
          { headers: this.getAuthHeaders() }
        );

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        this.tasksList = data.tasks || [];
      } catch (error) {
        console.error('Error loading tasks:', error);
        throw error;
      }
    },

    availableCommandOptions() {
      const commands = [...this.templateCommandOptions];
      for (const command of this.powershellCommandList || []) {
        if (!commands.includes(command.name)) {
          commands.push(command.name);
        }
      }
      return commands;
    },

    availableTemplateCommands() {
      return this.availableCommandOptions();
    },

    async loadPowerShellCommands() {
      try {
        const response = await fetch(`${this.apiBaseUrl}/powershell-commands`, {
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        this.powershellCommandList = data.commands || [];
      } catch (error) {
        console.error('Error loading PowerShell commands:', error);
        throw error;
      }
    },

    pasteSampleCustomCommand() {
      this.newCommand = {
        command_id: '',
        name: 'Get-ADUserCustom',
        description: 'Récupère la liste des comptes AD',
        script: 'Get-ADUser -Filter * | Select-Object Name, SamAccountName, Enabled',
        created_by: 'admin'
      };
    },

    resetCommandForm() {
      this.newCommand = {
        command_id: '',
        name: '',
        description: '',
        script: '',
        created_by: 'admin'
      };
      this.commandFormMode = 'create';
      this.showCommandForm = false;
    },

    openCommandForm(mode = 'create', command = null) {
      this.commandFormMode = mode;
      this.showCommandForm = true;
      if (mode === 'edit' && command) {
        this.newCommand = {
          command_id: command.command_id,
          name: command.name,
          description: command.description || '',
          script: command.script || '',
          created_by: command.created_by || 'admin'
        };
        return;
      }

      this.newCommand = {
        command_id: '',
        name: '',
        description: '',
        script: '',
        created_by: 'admin'
      };
    },

    toggleCommandSelection(commandId) {
      if (this.commandTableSelection.includes(commandId)) {
        this.commandTableSelection = this.commandTableSelection.filter(id => id !== commandId);
      } else {
        this.commandTableSelection.push(commandId);
      }
    },

    toggleSelectAllCommands() {
      if (this.commandTableSelection.length === this.powershellCommandList.length) {
        this.commandTableSelection = [];
      } else {
        this.commandTableSelection = this.powershellCommandList.map(command => command.command_id);
      }
    },

    exportSelectedCommands() {
      const selectedCommands = this.powershellCommandList.filter(command =>
        this.commandTableSelection.includes(command.command_id)
      );

      if (!selectedCommands.length) {
        return;
      }

      const data = JSON.stringify(selectedCommands, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const fileName = selectedCommands.length === 1
        ? `${selectedCommands[0].name.replace(/[^a-z0-9-_]+/gi, '-').toLowerCase()}.json`
        : 'commandes-export.json';
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },

    createCompositeCommand() {
      const selectedCommands = this.powershellCommandList.filter(command =>
        this.commandTableSelection.includes(command.command_id)
      );

      if (!selectedCommands.length) {
        return;
      }

      const combinedScript = selectedCommands
        .map((command) => `# ${command.name}\n${command.script || ''}`)
        .join('\n\n');

      this.newCommand = {
        command_id: '',
        name: `Composite-${Date.now()}`,
        description: selectedCommands.map((command) => command.name).join(', '),
        script: combinedScript,
        created_by: 'admin'
      };
      this.commandTableSelection = [];
      this.commandFormMode = 'create';
      this.showCommandForm = true;
    },

    async uploadCommandScript(event) {
      const file = event.target.files?.[0];
      if (!file) return;

      try {
        const scriptText = await file.text();
        this.newCommand = {
          command_id: this.newCommand.command_id || '',
          name: this.newCommand.name || file.name.replace(/\.[^.]+$/, ''),
          description: this.newCommand.description || `Script importé depuis ${file.name}`,
          script: scriptText.trim(),
          created_by: this.newCommand.created_by || 'admin'
        };
        event.target.value = '';
      } catch (error) {
        console.error('Error reading script:', error);
        alert('Impossible de lire le script importé.');
      }
    },

    async saveCommand() {
      if (!this.newCommand.name || !this.newCommand.script) {
        return;
      }

      this.isLoading = true;
      try {
        const url = this.newCommand.command_id
          ? `${this.apiBaseUrl}/powershell-commands/${this.newCommand.command_id}`
          : `${this.apiBaseUrl}/powershell-commands`;
        const method = this.newCommand.command_id ? 'PUT' : 'POST';

        const response = await fetch(url, {
          method,
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            name: this.newCommand.name,
            description: this.newCommand.description,
            script: this.newCommand.script,
            created_by: this.newCommand.created_by || 'admin'
          })
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        await this.loadPowerShellCommands();
        this.resetCommandForm();
      } catch (error) {
        console.error('Error saving PowerShell command:', error);
      } finally {
        this.isLoading = false;
      }
    },

    editCommand(command) {
      this.commandFormMode = 'edit';
      this.showCommandForm = true;
      this.newCommand = {
        command_id: command.command_id,
        name: command.name,
        description: command.description || '',
        script: command.script || '',
        created_by: command.created_by || 'admin'
      };
    },

    async deleteCommand(commandId) {
      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/powershell-commands/${commandId}`, {
          method: 'DELETE',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        this.resetCommandForm();
        await this.loadPowerShellCommands();
      } catch (error) {
        console.error('Error deleting PowerShell command:', error);
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Create a new audit task
     */
    async createTask() {
      if (!this.newTask.agentId || !this.newTask.command) {
        alert('Veuillez sélectionner un agent et une commande');
        return;
      }

      this.isLoading = true;

      try {
        // Parse parameters JSON
        let parameters = {};
        if (this.newTask.parametersJson && this.newTask.parametersJson.trim()) {
          try {
            parameters = JSON.parse(this.newTask.parametersJson);
          } catch (e) {
            alert('Paramètres JSON invalides');
            this.isLoading = false;
            return;
          }
        }

        const response = await fetch(
          `${this.apiBaseUrl}/tasks/${this.newTask.agentId}`,
          {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
              command: this.newTask.command,
              parameters: parameters,
              priority: this.newTask.priority
            })
          }
        );

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        alert(`Tâche créée avec succès!\nID: ${data.task_id}`);
        
        // Reset form
        this.newTask = {
          agentId: '',
          command: '',
          priority: 0,
          parametersJson: '{}'
        };

        // Reload tasks list
        await this.loadTasks();
      } catch (error) {
        console.error('Error creating task:', error);
        alert(`Erreur lors de la création de la tâche: ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Load results data
     */
    async loadResults() {
      try {
        const response = await fetch(
          `${this.apiBaseUrl}/monitoring/results`,
          { headers: this.getAuthHeaders() }
        );

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        this.resultsList = data.results || [];
      } catch (error) {
        console.error('Error loading results:', error);
        throw error;
      }
    },

    /**
     * Load stored audit templates
     */
    async loadAuditTemplates() {
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates`, {
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        this.templatesList = (data.templates || []).map(template => ({
          ...template,
          commands: Array.isArray(template?.commands) ? template.commands : []
        }));
      } catch (error) {
        console.error('Error loading audit templates:', error);
        throw error;
      }
    },

    async loadTemplateHistory() {
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/history`, {
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        this.templateHistory = data.history || [];
      } catch (error) {
        console.error('Error loading template history:', error);
        throw error;
      }
    },

    normalizeAuditTemplate(template = null) {
      const base = template || this.auditTemplate || {};
      const commands = Array.isArray(base.commands) ? base.commands : [];
      this.auditTemplate = {
        name: base.name || '',
        description: base.description || '',
        commands,
        created_by: base.created_by || 'admin'
      };
      return this.auditTemplate;
    },

    getRuleStatus(result) {
      if (result?.rule_status) {
        return result.rule_status;
      }

      const compliance = result?.compliance || {};
      if (compliance.status === 'non_compliant') return 'fail';
      if (compliance.status === 'partially_compliant') return 'warn';
      if (compliance.status === 'compliant') return 'success';

      const controls = Array.isArray(compliance.controls) ? compliance.controls : [];
      if (controls.some(control => String(control?.status || '').toUpperCase() === 'WARNING')) return 'warn';
      if (controls.length) return 'success';
      return '';
    },

    getRuleStatusLabel(result) {
      const status = this.getRuleStatus(result);
      if (status === 'success') return 'Conforme';
      if (status === 'fail') return 'Non conforme';
      if (status === 'warn') return 'Partiellement conforme';
      return '';
    },

    getComplianceStatusLabel(result) {
      const compliance = result?.compliance || {};
      if (compliance.status === 'non_compliant') return 'Non conforme';
      if (compliance.status === 'partially_compliant') return 'Partiellement conforme';
      if (compliance.status === 'compliant') return 'Conforme';
      const controls = Array.isArray(compliance.controls) ? compliance.controls : [];
      if (controls.some(control => String(control?.status || '').toUpperCase() === 'WARNING')) return 'Partiellement conforme';
      if (controls.length) return 'Conforme';
      return 'Non auditable';
    },

    getComplianceStatusClass(result) {
      const compliance = result?.compliance || {};
      if (compliance.status === 'non_compliant') return 'fail';
      if (compliance.status === 'partially_compliant') return 'warn';
      if (compliance.status === 'compliant') return 'success';
      const controls = Array.isArray(compliance.controls) ? compliance.controls : [];
      if (controls.some(control => String(control?.status || '').toUpperCase() === 'WARNING')) return 'warn';
      if (controls.length) return 'success';
      return 'empty';
    },

    getBusinessStatusClass(result) {
      const compliance = result?.compliance || {};
      if (compliance.status === 'non_compliant' || result?.status === 'failed') return 'failed';
      if (compliance.status === 'partially_compliant') return 'warning';
      if (compliance.status === 'compliant' || result?.status === 'success') return 'success';
      return 'success';
    },

    getBusinessStatusLabel(result) {
      const compliance = result?.compliance || {};
      if (compliance.status === 'non_compliant' || result?.status === 'failed') return '⚠️ Non conforme';
      if (compliance.status === 'partially_compliant') return '⚠️ Partiellement conforme';
      if (compliance.status === 'compliant' || result?.status === 'success') return '✅ Conforme';
      return '—';
    },

    getRuleStatusClass(result) {
      const status = this.getRuleStatus(result);
      return status ? status : 'empty';
    },

    getInactivityDuration(lastBeacon) {
      if (!lastBeacon) return 'Jamais';

      const now = new Date();
      const last = new Date(lastBeacon);
      const diffMs = now - last;
      const diffSeconds = Math.max(0, Math.floor(diffMs / 1000));

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

    formatDate(value) {
      if (!value) return '—';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    refreshTemplateSummary() {
      const commands = Array.isArray(this.auditTemplate?.commands) ? this.auditTemplate.commands : [];
      if (!commands.length) {
        this.templateBuilderSummary = 'Aucune commande ajoutée';
        return;
      }

      const coverage = Math.min(100, Math.round((commands.length / 10) * 100));
      this.templateBuilderSummary = `${commands.length} commandes préparées • couverture ${coverage}%`;
    },

    addTemplateCommand(command) {
      if (!command) return;
      const value = typeof command === 'string' ? command : command?.name || '';
      const commands = Array.isArray(this.auditTemplate?.commands) ? this.auditTemplate.commands : [];
      if (!value || commands.includes(value)) {
        return;
      }
      commands.push(value);
      this.auditTemplate.commands = commands;
      this.templateCommandSelection = '';
      this.refreshTemplateSummary();
    },

    removeTemplateCommand(index) {
      const commands = Array.isArray(this.auditTemplate?.commands) ? this.auditTemplate.commands : [];
      commands.splice(index, 1);
      this.auditTemplate.commands = commands;
      this.refreshTemplateSummary();
    },

    resetTemplateForm() {
      this.showTemplateForm = false;
      this.templateFormMode = 'create';
      this.selectedTemplateId = '';
      this.auditTemplate = {
        name: '',
        description: '',
        commands: [],
        created_by: 'admin'
      };
      this.refreshTemplateSummary();
    },

    selectResult(result) {
      this.selectedResultId = result.result_id;
      this.showResultModal = true;
    },

    closeResultModal() {
      this.showResultModal = false;
      this.selectedResultId = null;
    },

    openTemplateForm(mode = 'create', template = null) {
      this.templateFormMode = mode;
      this.showTemplateForm = true;

      if (mode === 'edit' && template) {
        this.selectedTemplateId = template.template_id || '';
        this.auditTemplate = {
          name: template.name,
          description: template.description || '',
          commands: [...(template.commands || [])],
          created_by: template.created_by || 'admin'
        };
      } else {
        this.selectedTemplateId = '';
        this.auditTemplate = {
          name: '',
          description: '',
          commands: [],
          created_by: 'admin'
        };
      }

      this.refreshTemplateSummary();
    },

    getActiveAgents() {
      return (this.agentsList || []).filter(agent => agent.status === 'active');
    },

    async sendAuditToAgent(agentId) {
      const templateId = this.auditTemplateSelection || this.selectedTemplateForApplication || this.selectedTemplateId;
      if (!templateId) {
        alert('Sélectionnez un template d’audit avant l’envoi.');
        return;
      }

      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/apply/${agentId}`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json().catch(() => ({}));
        this.agentDispatchStats[agentId] = Number(data.task_count || 0);
        await this.loadTasks();
      } catch (error) {
        console.error('Error sending audit to agent:', error);
        alert(`Erreur lors de l’envoi de l’audit : ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    toggleAgentSelection(agentId) {
      if (this.agentTableSelection.includes(agentId)) {
        this.agentTableSelection = this.agentTableSelection.filter(id => id !== agentId);
      } else {
        this.agentTableSelection.push(agentId);
      }
    },

    toggleSelectAllActiveAgents() {
      const activeAgents = this.getActiveAgents();
      if (this.agentTableSelection.length === activeAgents.length && activeAgents.length > 0) {
        this.agentTableSelection = [];
      } else {
        this.agentTableSelection = activeAgents.map(agent => agent.agent_id);
      }
    },

    async applyTemplateToSelectedAgents() {
      const templateId = this.auditTemplateSelection || this.selectedTemplateForApplication || this.selectedTemplateId;
      const activeAgents = this.getActiveAgents();
      const targetAgents = this.agentTableSelection.length
        ? activeAgents.filter(agent => this.agentTableSelection.includes(agent.agent_id))
        : activeAgents;

      if (!templateId) {
        alert('Sélectionnez un template d’audit.');
        return;
      }

      if (!targetAgents.length) {
        alert('Sélectionnez au moins un agent actif.');
        return;
      }

      this.isLoading = true;
      try {
        let totalTasks = 0;

        for (const agent of targetAgents) {
          const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/apply/${agent.agent_id}`, {
            method: 'POST',
            headers: this.getAuthHeaders()
          });

          if (response.status === 401) {
            this.logout();
            return;
          }

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
          }

          const data = await response.json().catch(() => ({}));
          totalTasks += Number(data.task_count || 0);
        }

        this.agentTableSelection = [];
        alert(`Audit envoyé à ${targetAgents.length} agent(s) : ${totalTasks} tâche(s) créée(s).`);
        await this.loadTasks();
      } catch (error) {
        console.error('Error applying template to selected agents:', error);
        alert(`Erreur lors de l’envoi de l’audit : ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    async applyTemplateToAllActiveAgents() {
      const templateId = this.auditTemplateSelection || this.selectedTemplateForApplication || this.selectedTemplateId;
      const activeAgents = this.getActiveAgents();

      if (!templateId) {
        alert('Sélectionnez un template d’audit.');
        return;
      }

      if (!activeAgents.length) {
        alert('Aucun agent actif disponible pour recevoir l’audit.');
        return;
      }

      this.isLoading = true;
      try {
        let totalTasks = 0;

        for (const agent of activeAgents) {
          const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/apply/${agent.agent_id}`, {
            method: 'POST',
            headers: this.getAuthHeaders()
          });

          if (response.status === 401) {
            this.logout();
            return;
          }

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
          }

          const data = await response.json().catch(() => ({}));
          totalTasks += Number(data.task_count || 0);
        }

        this.agentTableSelection = [];
        alert(`Audit envoyé à tous les agents actifs : ${totalTasks} tâche(s) créée(s).`);
        await this.loadTasks();
      } catch (error) {
        console.error('Error applying template to all active agents:', error);
        alert(`Erreur lors de l’envoi global : ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    toggleTemplateSelection(templateId) {
      if (this.templateTableSelection.includes(templateId)) {
        this.templateTableSelection = this.templateTableSelection.filter(id => id !== templateId);
      } else {
        this.templateTableSelection.push(templateId);
      }
    },

    toggleSelectAllTemplates() {
      if (this.templateTableSelection.length === this.templatesList.length) {
        this.templateTableSelection = [];
      } else {
        this.templateTableSelection = this.templatesList.map(template => template.template_id);
      }
    },

    async exportSelectedTemplates() {
      const selectedTemplates = this.templatesList.filter(template =>
        this.templateTableSelection.includes(template.template_id)
      );

      if (!selectedTemplates.length) {
        return;
      }

      const payload = selectedTemplates.length === 1
        ? selectedTemplates[0]
        : { templates: selectedTemplates, exported_at: new Date().toISOString() };

      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = selectedTemplates.length === 1
        ? `${(selectedTemplates[0].name || 'template').replace(/\s+/g, '-').toLowerCase()}.json`
        : 'templates-export.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },

    async duplicateTemplate(templateId) {
      if (!templateId) return;
      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/duplicate`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error duplicating template:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async duplicateSelectedTemplates() {
      if (!this.templateTableSelection.length) return;

      this.isLoading = true;
      try {
        const duplicates = this.templateTableSelection.slice();
        for (const templateId of duplicates) {
          const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/duplicate`, {
            method: 'POST',
            headers: this.getAuthHeaders()
          });

          if (response.status === 401) {
            this.logout();
            return;
          }

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
          }
        }

        this.templateTableSelection = [];
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error duplicating selected templates:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async deleteTemplate(templateId) {
      if (!templateId) return;
      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}`, {
          method: 'DELETE',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        this.templateTableSelection = this.templateTableSelection.filter(id => id !== templateId);
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async deleteSelectedTemplates() {
      if (!this.templateTableSelection.length) return;
      const confirmed = window.confirm('Supprimer les templates sélectionnés ?');
      if (!confirmed) return;

      this.isLoading = true;
      try {
        for (const templateId of [...this.templateTableSelection]) {
          const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders()
          });

          if (response.status === 401) {
            this.logout();
            return;
          }

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
          }
        }

        this.templateTableSelection = [];
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error deleting selected templates:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async importTemplateFile(event) {
      const file = event.target.files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        const payload = {
          name: parsed.name || file.name.replace(/\.[^.]+$/, ''),
          description: parsed.description || 'Template importé',
          commands: Array.isArray(parsed.commands) ? parsed.commands : [],
          created_by: parsed.created_by || 'admin'
        };

        if (!payload.commands.length) {
          throw new Error('Le fichier JSON doit contenir une liste de commandes.');
        }

        const response = await fetch(`${this.apiBaseUrl}/audit-templates`, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify(payload)
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        event.target.value = '';
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error importing template JSON:', error);
      }
    },

    loadTemplateIntoEditor(template) {
      if (!template) return;
      this.auditTemplate = {
        name: template.name,
        description: template.description || '',
        commands: [...(template.commands || [])],
        created_by: template.created_by || 'admin'
      };
      this.selectedTemplateId = template.template_id || '';
      this.refreshTemplateSummary();
      this.currentPage = 'templates';
    },

    loadDemoTemplate() {
      this.auditTemplate = {
        name: 'Audit système standard',
        description: 'Contrôle de sécurité rapide du poste et du réseau',
        commands: [
          'Get-Process',
          'Get-Service',
          'Get-LocalUser',
          'Get-IPConfig',
          'Get-EventLog'
        ],
        created_by: 'admin'
      };
      this.refreshTemplateSummary();
    },

    async importTemplateFromJsonText() {
      const raw = (this.templateJsonInput || '').trim();
      if (!raw) {
        alert('Collez un JSON de template avant d’importer.');
        return;
      }

      try {
        const parsed = JSON.parse(raw);
        const payload = {
          name: parsed.name || 'Template importé',
          description: parsed.description || 'Importé depuis JSON',
          commands: Array.isArray(parsed.commands) ? parsed.commands : [],
          created_by: parsed.created_by || 'admin'
        };

        if (!payload.commands.length) {
          throw new Error('Le JSON doit contenir un tableau commands.');
        }

        this.auditTemplate = payload;
        this.refreshTemplateSummary();
        this.templateJsonInput = '';
        alert('Template importé dans l’éditeur. Vous pouvez maintenant le valider et le sauvegarder.');
      } catch (error) {
        console.error('Error parsing JSON template:', error);
        alert(`JSON invalide : ${error.message}`);
      }
    },

    async createAuditTemplate() {
      if (!this.auditTemplate.name.trim()) {
        return;
      }

      if (!this.auditTemplate.commands.length) {
        return;
      }

      this.isLoading = true;
      this.refreshTemplateSummary();

      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates`, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify(this.auditTemplate)
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        this.auditTemplate = { name: '', description: '', commands: [], created_by: 'admin' };
        this.refreshTemplateSummary();
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error creating audit template:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async updateSelectedTemplate() {
      if (!this.selectedTemplateId) {
        return;
      }

      if (!this.auditTemplate.name.trim() || !this.auditTemplate.commands.length) {
        return;
      }

      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${this.selectedTemplateId}`, {
          method: 'PUT',
          headers: this.getAuthHeaders(),
          body: JSON.stringify(this.auditTemplate)
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error updating template:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async duplicateSelectedTemplate() {
      if (!this.selectedTemplateId) {
        return;
      }

      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${this.selectedTemplateId}/duplicate`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error duplicating template:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async deleteSelectedTemplate() {
      if (!this.selectedTemplateId) {
        return;
      }

      if (!confirm('Supprimer ce template ?')) {
        return;
      }

      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${this.selectedTemplateId}`, {
          method: 'DELETE',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        this.selectedTemplateId = '';
        this.auditTemplate = { name: '', description: '', commands: [], created_by: 'admin' };
        this.refreshTemplateSummary();
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async exportSelectedTemplate() {
      if (!this.selectedTemplateId) {
        alert('Sélectionnez un template à exporter.');
        return;
      }

      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${this.selectedTemplateId}/export`, {
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const payload = await response.json();
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${(payload.name || 'template').replace(/\s+/g, '-').toLowerCase()}.json`;
        link.click();
        URL.revokeObjectURL(url);
        alert('Export JSON du template généré.');
      } catch (error) {
        console.error('Error exporting template:', error);
        alert(`Erreur lors de l'export : ${error.message}`);
      }
    },

    async uploadAuditTemplateFile(event) {
      const file = event.target.files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        const payload = {
          name: parsed.name || file.name.replace(/\.[^.]+$/, ''),
          description: parsed.description || 'Template importé',
          commands: Array.isArray(parsed.commands) ? parsed.commands : [],
          created_by: parsed.created_by || 'admin'
        };

        if (!payload.commands.length) {
          throw new Error('Le fichier JSON doit contenir une propriété commands');
        }

        const response = await fetch(`${this.apiBaseUrl}/audit-templates`, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify(payload)
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const created = await response.json();
        alert(`Template importé : ${created.name}`);
        event.target.value = '';
        await this.loadAuditTemplates();
      } catch (error) {
        console.error('Error importing audit template:', error);
        alert(`Erreur lors de l'import : ${error.message}`);
      }
    },

    async applyTemplateToAgent() {
      const templateId = this.selectedTemplateForApplication || this.selectedTemplateId;
      const agentId = this.newTask.agentId;

      if (!templateId) {
        alert('Sélectionnez un template avant de l\'appliquer.');
        return;
      }

      if (!agentId) {
        alert('Sélectionnez un agent cible.');
        return;
      }

      this.isLoading = true;

      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/apply/${agentId}`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        alert(`Template appliqué : ${result.task_count} tâches créées pour l'agent.`);
        await this.loadTasks();
        await this.loadTemplateHistory();
      } catch (error) {
        console.error('Error applying template:', error);
        alert(`Erreur lors de l'application du template : ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    quickApplyTemplate(templateId) {
      if (!templateId) {
        alert('Aucun template sélectionné.');
        return;
      }

      if (!this.newTask.agentId) {
        this.selectedTemplateForApplication = templateId;
        alert('Sélectionnez d\'abord un agent cible dans le formulaire, puis appliquez à nouveau.');
        return;
      }

      this.selectedTemplateForApplication = templateId;
      this.applyTemplateToAgent();
    },

    async applyTemplateToAllAgents() {
      if (!this.selectedTemplateForApplication && !this.selectedTemplateId) {
        alert('Sélectionnez un template à déployer à tous les agents.');
        return;
      }

      const templateId = this.selectedTemplateForApplication || this.selectedTemplateId;

      this.isLoading = true;
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates/${templateId}/apply-all`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        alert(`Déploiement global terminé : ${result.task_count} tâches créées pour ${result.agents_total} agent(s).`);
        await this.loadTasks();
        await this.loadTemplateHistory();
      } catch (error) {
        console.error('Error applying template to all agents:', error);
        alert(`Erreur lors du déploiement global : ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    async exportAllTemplates() {
      try {
        const response = await fetch(`${this.apiBaseUrl}/audit-templates`, {
          headers: this.getAuthHeaders()
        });

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        const payload = {
          exported_at: new Date().toISOString(),
          templates: data.templates || []
        };

        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'audit-templates-bundle.json';
        link.click();
        URL.revokeObjectURL(url);
        alert('Bundle de templates exporté.');
      } catch (error) {
        console.error('Error exporting all templates:', error);
        alert(`Erreur lors de l'export du bundle : ${error.message}`);
      }
    },

    /**
     * Load alerts data
     */
    async loadAlerts() {
      try {
        const response = await fetch(
          `${this.apiBaseUrl}/monitoring/alerts`,
          { headers: this.getAuthHeaders() }
        );

        if (response.status === 401) {
          throw new Error('Unauthorized');
        }

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        this.alertsList = Array.isArray(data.alerts) ? data.alerts : [];
      } catch (error) {
        console.error('Error loading alerts:', error);
        throw error;
      }
    },

    getAlertLevelClass(level) {
      const normalized = (level || '').toLowerCase();
      if (normalized === 'critical') return 'danger';
      if (normalized === 'warning') return 'warning';
      return 'success';
    },

    getComplianceLabel(value) {
      if (!value) return 'Conforme';
      if (value === 'non_compliant') return 'Non conforme';
      if (value === 'partially_compliant') return 'Partiellement conforme';
      return 'Conforme';
    },

    /**
     * Refresh current page data
     */
    async refreshData() {
      await this.loadPageData(this.currentPage);
    },

    /**
     * Delete an agent
     */
    async deleteAgent(agentId, agentName) {
      if (!confirm(`Êtes-vous sûr de vouloir supprimer l'agent "${agentName}"? Toutes les tâches et résultats associés seront également supprimés.`)) {
        return;
      }

      this.isLoading = true;

      try {
        const response = await fetch(
          `${this.apiBaseUrl}/agents/${agentId}`,
          {
            method: 'DELETE',
            headers: this.getAuthHeaders()
          }
        );

        if (response.status === 401) {
          this.logout();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        alert(`Agent supprimé avec succès: ${data.message}`);
        
        // Reload agents list
        await this.loadAgents();
      } catch (error) {
        console.error('Error deleting agent:', error);
        alert(`Erreur lors de la suppression de l'agent: ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Get authorization headers with JWT token
     */
    getAuthHeaders() {
      return {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      };
    },

    /**
     * Toggle result detail view
     */
    toggleResultDetail(resultId) {
      if (this.selectedResultId === resultId && this.showResultModal) {
        this.closeResultModal();
        return;
      }

      this.selectedResultId = resultId;
      this.showResultModal = true;
    },

    /**
     * Confirm logout
     */
    confirmLogout() {
      if (confirm('Êtes-vous sûr de vouloir vous déconnecter?')) {
        this.logout();
      }
    },

    /**
     * Logout and redirect
     */
    logout() {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_token_exp');
      window.location.href = 'admin-login.html?logout=true';
    }
  }
}).mount('#app');
