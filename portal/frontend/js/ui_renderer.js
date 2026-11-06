/**
 * Kant Compiler Toolchain - UI Rendering Engine
 * Modular DOM rendering for stage cards, task checklists, and metrics.
 */

export class UIRenderer {
  constructor(store, options = {}) {
    this.store = store;
    this.filter = {
      status: 'ALL', // 'ALL' | 'INCOMPLETE' | 'DONE'
      agent: 'ALL',
      search: ''
    };

    // Cached DOM elements
    this.elements = {
      totalTasks: document.getElementById('stat-total-tasks'),
      completedTasks: document.getElementById('stat-completed-tasks'),
      blockedTasks: document.getElementById('stat-blocked-tasks'),
      progressPct: document.getElementById('stat-progress-pct'),
      progressBarFill: document.getElementById('progress-bar-fill'),
      stageCardsContainer: document.getElementById('stage-cards-container'),
      drawerContainer: document.getElementById('stage-detail-drawer'),
      searchInput: document.getElementById('task-search-input'),
    };

    this.bindSearchInput();
  }

  bindSearchInput() {
    if (this.elements.searchInput) {
      this.elements.searchInput.addEventListener('input', (e) => {
        this.filter.search = e.target.value.trim().toLowerCase();
        this.renderStageCards();
        this.renderDrawer();
      });
    }
  }

  setFilter(filterUpdates) {
    Object.assign(this.filter, filterUpdates);
    this.renderStageCards();
    this.renderDrawer();
  }

  renderAll() {
    this.renderMetrics();
    this.renderStageCards();
    this.renderDrawer();
  }

  renderMetrics() {
    const state = this.store.getState();
    if (!state || !state.global_stats) return;

    const stats = state.global_stats;
    if (this.elements.totalTasks) this.elements.totalTasks.textContent = stats.total_tasks;
    if (this.elements.completedTasks) this.elements.completedTasks.textContent = stats.completed_tasks;
    if (this.elements.blockedTasks) this.elements.blockedTasks.textContent = stats.blocked_tasks;
    if (this.elements.progressPct) this.elements.progressPct.textContent = `${stats.progress_percent.toFixed(1)}%`;
    if (this.elements.progressBarFill) this.elements.progressBarFill.style.width = `${stats.progress_percent}%`;
  }

  renderStageCards() {
    const container = this.elements.stageCardsContainer;
    if (!container) return;

    const state = this.store.getState();
    if (!state || !state.circles) return;

    container.innerHTML = '';
    const activeCircleId = this.store.getActiveCircleId();

    for (const circle of state.circles) {
      const isActive = circle.id === activeCircleId;
      const isLocked = circle.gate_status === 'LOCKED';

      // Compute task stats for this circle
      let circleTotal = 0;
      let circleDone = 0;
      for (const h of circle.main_headings || []) {
        for (const s of h.sub_headings || []) {
          for (const t of s.tasks || []) {
            circleTotal += 1;
            if (t.status === 'DONE' || t.status === 'DONE_VERIFIED') {
              circleDone += 1;
            }
          }
        }
      }

      const card = document.createElement('div');
      card.className = `stage-card ${isActive ? 'active' : ''} ${isLocked ? 'locked' : ''}`;
      card.dataset.circleId = circle.id;

      card.innerHTML = `
        <div class="stage-card-header">
          <div class="stage-card-title-group">
            <span class="stage-id-badge">${circle.id}</span>
            <div>
              <div class="stage-card-name">${escapeHtml(circle.short_title || circle.name)}</div>
              <div class="stage-card-wave">${escapeHtml(circle.wave || '')}</div>
            </div>
          </div>
          <span class="stage-status-badge ${(circle.gate_status || 'PENDING').toLowerCase()}">${circle.gate_status || 'PENDING'}</span>
        </div>
        <div class="stage-progress-row">
          <div class="stage-progress-track">
            <div class="stage-progress-fill" style="width: ${circleTotal > 0 ? (circleDone / circleTotal) * 100 : 0}%"></div>
          </div>
          <span class="stage-progress-num">${circleDone} / ${circleTotal} Tasks</span>
        </div>
      `;

      card.addEventListener('click', () => {
        this.store.setActiveCircleId(circle.id);
        this.renderStageCards();
        this.renderDrawer();
      });

      container.appendChild(card);
    }
  }

  renderDrawer() {
    const drawer = this.elements.drawerContainer;
    if (!drawer) return;

    const circle = this.store.getActiveCircle();
    if (!circle) {
      drawer.innerHTML = `
        <div class="drawer-body" style="justify-content: center; align-items: center; color: var(--color-text-muted);">
          Select a pipeline stage to inspect task checklist and formal gates.
        </div>
      `;
      return;
    }

    const gateStatus = circle.gate_status || 'PENDING';
    const checklist = circle.gate_checklist || {};

    let html = `
      <div class="drawer-header">
        <div>
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span class="stage-id-badge">${circle.id}</span>
            <span class="stage-status-badge ${gateStatus.toLowerCase()}">${gateStatus}</span>
          </div>
          <h2 style="font-size: var(--font-size-md); font-weight: 700; color: var(--color-text-primary); margin-bottom: 2px;">
            ${escapeHtml(circle.name)}
          </h2>
          <div style="font-size: var(--font-size-xs); color: var(--color-gold-light);">
            ${escapeHtml(circle.wave || '')}
          </div>
        </div>
      </div>

      <div class="drawer-body">
        <!-- Verification Gate Checklist Card -->
        <div class="gate-card">
          <div class="gate-card-title">
            <span>Epistemological Gate Checklist</span>
            <select class="form-control" id="gate-status-select" style="font-size: 11px; padding: 2px 6px;">
              <option value="PENDING" ${gateStatus === 'PENDING' ? 'selected' : ''}>PENDING</option>
              <option value="ACTIVE" ${gateStatus === 'ACTIVE' ? 'selected' : ''}>ACTIVE</option>
              <option value="PASSED" ${gateStatus === 'PASSED' ? 'selected' : ''}>PASSED</option>
              <option value="LOCKED" ${gateStatus === 'LOCKED' ? 'selected' : ''}>LOCKED</option>
            </select>
          </div>
          <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 4px;">
    `;

    for (const [key, val] of Object.entries(checklist)) {
      const label = key.replace(/_/g, ' ').toUpperCase();
      html += `
        <label class="gate-checklist-item">
          <input type="checkbox" class="task-checkbox" data-gate-key="${key}" ${val ? 'checked' : ''} style="width: 14px; height: 14px;">
          <span>${label}</span>
        </label>
      `;
    }

    html += `
          </div>
        </div>

        <!-- Task Groups & Tasks -->
        <div class="tasks-container">
    `;

    let totalRenderedTasks = 0;
    for (const heading of circle.main_headings || []) {
      const agent = heading.assigned_agent || 'SA-01';

      for (const sub of heading.sub_headings || []) {
        const filteredTasks = (sub.tasks || []).filter(task => {
          if (this.filter.status === 'INCOMPLETE' && (task.status === 'DONE' || task.status === 'DONE_VERIFIED')) {
            return false;
          }
          if (this.filter.status === 'DONE' && task.status !== 'DONE' && task.status !== 'DONE_VERIFIED') {
            return false;
          }
          if (this.filter.agent !== 'ALL' && agent !== this.filter.agent) {
            return false;
          }
          if (this.filter.search) {
            const query = this.filter.search;
            const matchesTitle = task.title.toLowerCase().includes(query);
            const matchesId = task.id.toLowerCase().includes(query);
            const matchesNotes = (task.notes || '').toLowerCase().includes(query);
            const matchesCmd = (task.verification_cmd || '').toLowerCase().includes(query);
            if (!matchesTitle && !matchesId && !matchesNotes && !matchesCmd) {
              return false;
            }
          }
          return true;
        });

        if (filteredTasks.length === 0) continue;

        html += `
          <div class="task-group">
            <div class="task-group-heading">
              <span>${escapeHtml(sub.title)}</span>
              <span class="task-group-lane">${escapeHtml(agent)} | ${escapeHtml(heading.crate_lane || '')}</span>
            </div>
        `;

        for (const task of filteredTasks) {
          totalRenderedTasks += 1;
          const isDone = task.status === 'DONE' || task.status === 'DONE_VERIFIED';
          const statusClass = isDone ? 'done' : (task.status === 'WIP' ? 'wip' : 'todo');

          html += `
            <div class="task-item ${isDone ? 'done' : ''}" data-task-id="${task.id}">
              <div class="task-item-top">
                <div class="task-title-wrap">
                  <input type="checkbox" class="task-checkbox" data-task-id="${task.id}" ${isDone ? 'checked' : ''}>
                  <div>
                    <span class="task-id-tag">${task.id}</span>
                    <span class="task-title-text">${escapeHtml(task.title)}</span>
                  </div>
                </div>
                <span class="task-status-pill ${statusClass}">${task.status}</span>
              </div>
              ${task.verification_cmd ? `
                <div class="task-cmd-block">
                  <code>$ ${escapeHtml(task.verification_cmd)}</code>
                </div>
              ` : ''}
              ${task.notes ? `
                <div class="task-notes">${escapeHtml(task.notes)}</div>
              ` : ''}
            </div>
          `;
        }

        html += `</div>`;
      }
    }

    if (totalRenderedTasks === 0) {
      html += `
        <div style="text-align: center; color: var(--color-text-muted); padding: var(--space-xl);">
          No tasks match the active filters.
        </div>
      `;
    }

    html += `
        </div>
      </div>
    `;

    drawer.innerHTML = html;
    this.bindDrawerEvents(circle.id);
  }

  bindDrawerEvents(circleId) {
    const drawer = this.elements.drawerContainer;
    if (!drawer) return;

    // Gate Status dropdown
    const gateSelect = drawer.querySelector('#gate-status-select');
    if (gateSelect) {
      gateSelect.addEventListener('change', (e) => {
        this.store.changeCircleGateStatus(circleId, e.target.value);
        this.renderStageCards();
      });
    }

    // Gate checklist toggles
    const gateCheckboxes = drawer.querySelectorAll('input[data-gate-key]');
    for (const cb of gateCheckboxes) {
      cb.addEventListener('change', (e) => {
        const key = e.target.getAttribute('data-gate-key');
        this.store.toggleGateCheck(circleId, key);
      });
    }

    // Task completion checkboxes
    const taskCheckboxes = drawer.querySelectorAll('input[data-task-id]');
    for (const cb of taskCheckboxes) {
      cb.addEventListener('change', (e) => {
        const taskId = e.target.getAttribute('data-task-id');
        const newStatus = e.target.checked ? 'DONE_VERIFIED' : 'TODO';
        this.store.updateTaskStatus(circleId, taskId, newStatus);
        this.renderMetrics();
        this.renderStageCards();
        this.renderDrawer();
      });
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
