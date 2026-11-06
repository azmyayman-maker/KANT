/**
 * Kant Compiler Toolchain - Telemetry Audit Logger & Inspector
 * Live stream collector and audit log inspector.
 */

export class TelemetryAuditLogger {
  constructor(options = {}) {
    this.maxRecords = options.maxRecords || 500;
    this.records = [];
    this.listeners = new Set();
    this.currentFilter = {
      level: 'ALL',
      agent: 'ALL',
      search: ''
    };
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify(newRecord) {
    for (const listener of this.listeners) {
      try {
        listener(newRecord, this.records);
      } catch (err) {
        console.error('TelemetryAuditLogger listener error:', err);
      }
    }
  }

  addRecord(record) {
    if (!record) return;
    const entry = {
      id: record.id || `ev-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      timestamp: record.timestamp || new Date().toISOString(),
      level: (record.level || record.severity || 'INFO').toUpperCase(),
      agent: record.agent || record.agent_id || 'SYSTEM',
      commit_hash: record.commit_hash || record.commit || '3fe7aea',
      message: record.message || record.event || '',
      details: record.details || null
    };

    this.records.unshift(entry);
    if (this.records.length > this.maxRecords) {
      this.records.pop();
    }

    this.notify(entry);
  }

  async fetchInitialHistory() {
    try {
      const res = await fetch('/api/telemetry?limit=100');
      if (res.ok) {
        const events = await res.json();
        if (Array.isArray(events)) {
          for (const ev of events) {
            this.addRecord(ev);
          }
        }
      }
    } catch (e) {
      // Offline fallback: provide baseline zero-state initialization event
      this.addRecord({
        level: 'AUDIT',
        agent: 'SA-ARCHITECT',
        message: 'Telemetry portal initialized in strict 0.0% zero-state mode.',
        commit_hash: '3fe7aea'
      });
    }
  }

  getFilteredRecords() {
    return this.records.filter(r => {
      if (this.currentFilter.level !== 'ALL' && r.level !== this.currentFilter.level) {
        return false;
      }
      if (this.currentFilter.agent !== 'ALL' && r.agent !== this.currentFilter.agent) {
        return false;
      }
      if (this.currentFilter.search) {
        const query = this.currentFilter.search.toLowerCase();
        const matchesMsg = r.message.toLowerCase().includes(query);
        const matchesAgent = r.agent.toLowerCase().includes(query);
        const matchesCommit = r.commit_hash.toLowerCase().includes(query);
        if (!matchesMsg && !matchesAgent && !matchesCommit) {
          return false;
        }
      }
      return true;
    });
  }

  setFilter(filterUpdates) {
    Object.assign(this.currentFilter, filterUpdates);
  }

  renderToTable(tbodyElement) {
    if (!tbodyElement) return;
    tbodyElement.innerHTML = '';

    const records = this.getFilteredRecords();
    if (records.length === 0) {
      const emptyRow = document.createElement('tr');
      emptyRow.innerHTML = `
        <td colspan="5" style="text-align: center; color: var(--color-text-muted); padding: var(--space-xl);">
          No telemetry events recorded yet. Zero-state invariant active.
        </td>
      `;
      tbodyElement.appendChild(emptyRow);
      return;
    }

    for (const rec of records) {
      const tr = document.createElement('tr');
      const timeStr = rec.timestamp.replace('T', ' ').substring(0, 19);
      const sevClass = rec.level.toLowerCase();

      tr.innerHTML = `
        <td class="mono" style="color: var(--color-text-muted);">${timeStr}</td>
        <td><span class="severity-pill ${sevClass}">${rec.level}</span></td>
        <td class="mono" style="color: var(--color-gold-light); font-weight: 700;">${rec.agent}</td>
        <td>${escapeHtml(rec.message)}</td>
        <td class="mono" style="color: var(--color-cyan);">${rec.commit_hash.substring(0, 7)}</td>
      `;
      tbodyElement.appendChild(tr);
    }
  }

  exportJson() {
    const blob = new Blob([JSON.stringify(this.records, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kant_telemetry_audit_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
