/**
 * Kant Compiler Toolchain - Telemetry Portal Bootstrap & Application Coordinator
 * Strictly decoupled ES6 modules architecture. Zero CDN dependencies.
 */

import { RoadmapStore } from './store.js';
import { SSEClient } from './sse_client.js';
import { TopologicalPipelineGraph } from './graph.js';
import { UIRenderer } from './ui_renderer.js';
import { TelemetryAuditLogger } from './audit_logger.js';

class KantPortalApp {
  constructor() {
    this.store = null;
    this.sseClient = null;
    this.graph = null;
    this.uiRenderer = null;
    this.auditLogger = null;
  }

  async init() {
    console.log('[KantPortalApp] Initializing modular telemetry portal...');

    // 1. Initialize State Store
    this.store = new RoadmapStore();

    // 2. Initialize Telemetry Audit Logger
    this.auditLogger = new TelemetryAuditLogger();

    // 3. Initialize UI Renderer
    this.uiRenderer = new UIRenderer(this.store);

    // 4. Initialize Topological Pipeline Graph
    const graphContainer = document.getElementById('pipeline-dag-container');
    if (graphContainer) {
      this.graph = new TopologicalPipelineGraph(graphContainer, {
        onNodeClick: (circleId) => {
          this.store.setActiveCircleId(circleId);
          this.uiRenderer.renderStageCards();
          this.uiRenderer.renderDrawer();
          this.graph.render(this.store.getState(), circleId);
        }
      });
    }

    // 5. Initialize SSE Client
    this.sseClient = new SSEClient('/api/events');

    // 6. Connect Store Subscriptions
    this.store.subscribe((state, event) => {
      this.uiRenderer.renderMetrics();
      if (event.type === 'ACTIVE_CIRCLE_CHANGED') {
        if (this.graph) {
          this.graph.render(state, event.circleId);
        }
      }
    });

    // 7. Connect SSE Event Streams
    this.setupSSEListeners();

    // 8. Connect Global Navigation & Action Listeners
    this.setupNavigation();
    this.setupFilterToolbar();
    this.setupThemeToggle();
    this.setupDistributionActions();
    this.setupStateExportImport();

    // 9. Initial Render & Sync
    this.uiRenderer.renderAll();
    if (this.graph) {
      this.graph.render(this.store.getState(), this.store.getActiveCircleId());
    }

    // 10. Fetch Server State & Initial Telemetry
    await this.store.fetchStateFromServer();
    this.uiRenderer.renderAll();
    if (this.graph) {
      this.graph.render(this.store.getState(), this.store.getActiveCircleId());
    }

    await this.auditLogger.fetchInitialHistory();
    this.renderAuditLogs();

    // 11. Connect SSE Broker
    this.sseClient.connect();

    console.log('[KantPortalApp] Initialization complete. Invariant 0.0% zero-state active.');
  }

  setupSSEListeners() {
    const pill = document.getElementById('connection-pill');
    const pillText = document.getElementById('connection-pill-text');

    this.sseClient.on('status_change', ({ status, attempts }) => {
      if (!pill || !pillText) return;
      pill.className = `connection-pill ${status}`;
      if (status === 'connected') {
        pillText.textContent = 'SSE LIVE';
      } else if (status === 'reconnecting') {
        pillText.textContent = `RETRYING (#${attempts})`;
      } else if (status === 'connecting') {
        pillText.textContent = 'CONNECTING';
      } else {
        pillText.textContent = 'OFFLINE';
      }
    });

    this.sseClient.on('state_update', (incomingState) => {
      console.log('[SSE] Live state update received:', incomingState);
      if (incomingState && incomingState.circles) {
        this.store.setState(incomingState, false);
        this.uiRenderer.renderAll();
        if (this.graph) {
          this.graph.render(this.store.getState(), this.store.getActiveCircleId());
        }
      }
    });

    this.sseClient.on('telemetry_event', (eventData) => {
      this.auditLogger.addRecord(eventData);
      this.renderAuditLogs();
    });

    this.auditLogger.subscribe(() => {
      this.renderAuditLogs();
    });
  }

  setupNavigation() {
    const tabButtons = document.querySelectorAll('.nav-tab-btn');
    const views = {
      'tab-pipeline': document.getElementById('view-pipeline'),
      'tab-audit': document.getElementById('view-audit'),
      'tab-dist': document.getElementById('view-dist'),
    };

    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabKey = btn.dataset.tab;
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        Object.values(views).forEach(v => {
          if (v) v.classList.remove('active');
        });

        if (views[tabKey]) {
          views[tabKey].classList.add('active');
        }

        if (tabKey === 'tab-pipeline' && this.graph) {
          this.graph.render(this.store.getState(), this.store.getActiveCircleId());
        } else if (tabKey === 'tab-audit') {
          this.renderAuditLogs();
        }
      });
    });

    // Graph zoom tools
    const zoomInBtn = document.getElementById('btn-zoom-in');
    const zoomOutBtn = document.getElementById('btn-zoom-out');
    const zoomResetBtn = document.getElementById('btn-zoom-reset');

    if (zoomInBtn && this.graph) zoomInBtn.addEventListener('click', () => this.graph.zoomIn());
    if (zoomOutBtn && this.graph) zoomOutBtn.addEventListener('click', () => this.graph.zoomOut());
    if (zoomResetBtn && this.graph) zoomResetBtn.addEventListener('click', () => this.graph.resetZoom());
  }

  setupFilterToolbar() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filterType = btn.dataset.filterStatus || 'ALL';
        this.uiRenderer.setFilter({ status: filterType });
      });
    });

    const agentSelect = document.getElementById('agent-filter-select');
    if (agentSelect) {
      agentSelect.addEventListener('change', (e) => {
        this.uiRenderer.setFilter({ agent: e.target.value });
      });
    }
  }

  setupThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (!toggleBtn) return;

    const savedTheme = localStorage.getItem('KANT_PORTAL_THEME') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);

    toggleBtn.addEventListener('click', () => {
      const current = document.body.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      document.body.setAttribute('data-theme', next);
      localStorage.setItem('KANT_PORTAL_THEME', next);
    });
  }

  setupDistributionActions() {
    const copyDistBtn = document.getElementById('btn-copy-dist-cmd');
    if (copyDistBtn) {
      copyDistBtn.addEventListener('click', () => {
        navigator.clipboard.writeText('bash scripts/distribute_v0_1.sh');
        copyDistBtn.textContent = 'Copied!';
        setTimeout(() => { copyDistBtn.textContent = 'Copy Command'; }, 2000);
      });
    }

    const copyInstallBtn = document.getElementById('btn-copy-install-cmd');
    if (copyInstallBtn) {
      copyInstallBtn.addEventListener('click', () => {
        navigator.clipboard.writeText('curl -fsSL https://raw.githubusercontent.com/azmyayman-maker/KANT/main/dist/v0.1.0/install.sh | sh');
        copyInstallBtn.textContent = 'Copied!';
        setTimeout(() => { copyInstallBtn.textContent = 'Copy Command'; }, 2000);
      });
    }
  }

  setupStateExportImport() {
    const exportBtn = document.getElementById('btn-export-state');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        const jsonStr = this.store.exportStateJson();
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kant_state_v01_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      });
    }

    const exportLogsBtn = document.getElementById('btn-export-audit-logs');
    if (exportLogsBtn) {
      exportLogsBtn.addEventListener('click', () => {
        this.auditLogger.exportJson();
      });
    }

    const importFileInput = document.getElementById('import-file-input');
    if (importFileInput) {
      importFileInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (evt) => {
          const success = this.store.importStateJson(evt.target.result);
          if (success) {
            this.uiRenderer.renderAll();
            if (this.graph) {
              this.graph.render(this.store.getState(), this.store.getActiveCircleId());
            }
            alert('Roadmap state imported successfully!');
          } else {
            alert('Failed to parse invalid JSON roadmap state.');
          }
        };
        reader.readAsText(file);
      });
    }
  }

  renderAuditLogs() {
    const tbody = document.getElementById('audit-table-tbody');
    if (tbody) {
      this.auditLogger.renderToTable(tbody);
    }
  }
}

// Bootstrap when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const app = new KantPortalApp();
  window.KantPortal = app;
  app.init().catch(err => {
    console.error('Fatal initialization error in KantPortalApp:', err);
  });
});
