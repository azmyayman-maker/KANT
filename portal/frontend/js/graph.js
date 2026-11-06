/**
 * Kant Compiler Toolchain - Topological Pipeline Dependency Graph (DAG)
 * Executive Light Design System: Interactive SVG visualization of Macro-Circles C0 through C6.
 * Zero Neon Glows, Pristine White Nodes, Imperial Bronze Accents, High Contrast.
 */

export class TopologicalPipelineGraph {
  constructor(containerElement, options = {}) {
    this.container = typeof containerElement === 'string'
      ? document.querySelector(containerElement)
      : containerElement;

    this.options = Object.assign({
      width: 1380,
      height: 290,
      nodeRadius: 36,
      onNodeClick: null,
    }, options);

    this.activeCircleId = 'C0';
    this.state = null;
    this.viewBox = { x: 0, y: 0, width: 1380, height: 290 };
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };

    this.stages = [
      { id: 'C0', wave: 'Pre-Wave', titleEn: 'Bootstrap & Invariants', titleAr: 'إقلاع مساحة العمل والثوابت' },
      { id: 'C1', wave: 'Wave 1', titleEn: 'Transcendental Aesthetic', titleAr: 'الجمالياء المجاوزة والـ AST' },
      { id: 'C2', wave: 'Wave 2', titleEn: 'Analytic & KANT-IR', titleAr: 'التحليلياء وشيم KANT-IR' },
      { id: 'C3', wave: 'Wave 3', titleEn: 'Dialectic & Noumena', titleAr: 'الجدلياء ونطاق النومان' },
      { id: 'C4', wave: 'Wave 4', titleEn: 'Method, VM & JIT', titleAr: 'مبحث المنهج والمفسر المزدوج' },
      { id: 'C5', wave: 'Wave 5', titleEn: 'Foundational Proofs', titleAr: 'براهين الجودة الأربعة' },
      { id: 'C6', wave: 'Wave 6', titleEn: 'Official v0.1 Release', titleAr: 'حزم الإطلاق والتوزيع v0.1' },
    ];

    this.initSvg();
  }

  initSvg() {
    if (!this.container) return;
    this.container.innerHTML = '';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `${this.viewBox.x} ${this.viewBox.y} ${this.viewBox.width} ${this.viewBox.height}`);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    this.svg = svg;

    // Defs for markers and subtle drop-shadows
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <marker id="arrow-gold" markerWidth="10" markerHeight="10" refX="8" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#936E22"/>
      </marker>
      <marker id="arrow-muted" markerWidth="10" markerHeight="10" refX="8" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#CBD5E1"/>
      </marker>
      <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.08"/>
      </filter>
      <filter id="node-active-shadow" x="-30%" y="-30%" width="160%" height="160%">
        <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#936E22" flood-opacity="0.18"/>
      </filter>
    `;
    svg.appendChild(defs);

    this.edgesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    this.edgesGroup.setAttribute('class', 'edges-layer');
    svg.appendChild(this.edgesGroup);

    this.nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    this.nodesGroup.setAttribute('class', 'nodes-layer');
    svg.appendChild(this.nodesGroup);

    this.setupInteractions();
    this.container.appendChild(svg);
  }

  setupInteractions() {
    this.svg.addEventListener('mousedown', (e) => {
      if (e.target.closest('.dag-node')) return;
      this.isPanning = true;
      this.panStart = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isPanning) return;
      const dx = (e.clientX - this.panStart.x) * (this.viewBox.width / this.container.clientWidth);
      const dy = (e.clientY - this.panStart.y) * (this.viewBox.height / this.container.clientHeight);
      this.viewBox.x -= dx;
      this.viewBox.y -= dy;
      this.panStart = { x: e.clientX, y: e.clientY };
      this.updateViewBox();
    });

    window.addEventListener('mouseup', () => {
      this.isPanning = false;
    });

    this.svg.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY > 0 ? 1.08 : 0.92;
      this.viewBox.width *= zoomFactor;
      this.viewBox.height *= zoomFactor;
      this.updateViewBox();
    });
  }

  updateViewBox() {
    this.svg.setAttribute('viewBox', `${this.viewBox.x} ${this.viewBox.y} ${this.viewBox.width} ${this.viewBox.height}`);
  }

  zoomIn() {
    this.viewBox.width *= 0.85;
    this.viewBox.height *= 0.85;
    this.updateViewBox();
  }

  zoomOut() {
    this.viewBox.width *= 1.15;
    this.viewBox.height *= 1.15;
    this.updateViewBox();
  }

  resetZoom() {
    this.viewBox = { x: 0, y: 0, width: 1380, height: 290 };
    this.updateViewBox();
  }

  render(state, activeCircleId) {
    this.state = state;
    this.activeCircleId = activeCircleId || 'C0';
    if (!this.svg) return;

    this.edgesGroup.innerHTML = '';
    this.nodesGroup.innerHTML = '';

    const count = this.stages.length;
    const startX = 110;
    const stepX = 190; // Generous 190px spacing between stages
    const centerY = 125;
    const r = this.options.nodeRadius; // 36px radius (72px diameter)

    const nodePositions = this.stages.map((stage, i) => ({
      ...stage,
      x: startX + i * stepX,
      y: centerY
    }));

    // Draw smooth cubic bezier edges
    for (let i = 0; i < nodePositions.length - 1; i++) {
      const from = nodePositions[i];
      const to = nodePositions[i + 1];
      const isPastActive = from.id === this.activeCircleId;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const startEdgeX = from.x + r + 3;
      const endEdgeX = to.x - r - 8;
      const dx = (endEdgeX - startEdgeX) / 2;

      path.setAttribute('d', `M ${startEdgeX} ${from.y} C ${startEdgeX + dx} ${from.y}, ${endEdgeX - dx} ${to.y}, ${endEdgeX} ${to.y}`);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', isPastActive ? '#936E22' : '#CBD5E1');
      path.setAttribute('stroke-width', isPastActive ? '2.5' : '2');
      path.setAttribute('stroke-linecap', 'round');
      path.setAttribute('stroke-dasharray', isPastActive ? 'none' : '5 4');
      path.setAttribute('marker-end', isPastActive ? 'url(#arrow-gold)' : 'url(#arrow-muted)');
      this.edgesGroup.appendChild(path);
    }

    // Draw prominent readable nodes
    for (const node of nodePositions) {
      const isActive = node.id === this.activeCircleId;
      const circleData = this.state && this.state.circles ? this.state.circles.find(c => c.id === node.id) : null;
      const gateStatus = circleData ? (circleData.gate_status || 'PENDING') : 'PENDING';

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', `dag-node ${isActive ? 'active' : ''}`);
      g.setAttribute('data-id', node.id);
      g.style.cursor = 'pointer';

      // Outer accent ring for active node
      if (isActive) {
        const outerRing = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        outerRing.setAttribute('cx', node.x);
        outerRing.setAttribute('cy', node.y);
        outerRing.setAttribute('r', r + 6);
        outerRing.setAttribute('fill', 'none');
        outerRing.setAttribute('stroke', '#F3E3B6');
        outerRing.setAttribute('stroke-width', '2.5');
        g.appendChild(outerRing);
      }

      // Base circle body
      const baseCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      baseCircle.setAttribute('cx', node.x);
      baseCircle.setAttribute('cy', node.y);
      baseCircle.setAttribute('r', r);
      baseCircle.setAttribute('fill', isActive ? '#FFFFFF' : (gateStatus === 'PASSED' ? '#FFFFFF' : '#F8FAFC'));
      baseCircle.setAttribute('stroke', isActive ? '#936E22' : (gateStatus === 'PASSED' ? '#059669' : '#CBD5E1'));
      baseCircle.setAttribute('stroke-width', isActive ? '3' : '2');
      baseCircle.setAttribute('filter', isActive ? 'url(#node-active-shadow)' : 'url(#node-shadow)');
      g.appendChild(baseCircle);

      // Node label ID (Large and bold)
      const textId = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      textId.setAttribute('x', node.x);
      textId.setAttribute('y', node.y + 6);
      textId.setAttribute('text-anchor', 'middle');
      textId.setAttribute('fill', isActive ? '#936E22' : '#0F172A');
      textId.setAttribute('font-family', 'ui-monospace, monospace');
      textId.setAttribute('font-size', '17px');
      textId.setAttribute('font-weight', '800');
      textId.textContent = node.id;
      g.appendChild(textId);

      // Wave tag (above node)
      const waveText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      waveText.setAttribute('x', node.x);
      waveText.setAttribute('y', node.y - r - 12);
      waveText.setAttribute('text-anchor', 'middle');
      waveText.setAttribute('fill', isActive ? '#7A5B18' : '#64748B');
      waveText.setAttribute('font-family', 'system-ui, sans-serif');
      waveText.setAttribute('font-size', '11.5px');
      waveText.setAttribute('font-weight', '700');
      waveText.textContent = node.wave;
      g.appendChild(waveText);

      // Title (English & primary, below node)
      const titleEn = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      titleEn.setAttribute('x', node.x);
      titleEn.setAttribute('y', node.y + r + 20);
      titleEn.setAttribute('text-anchor', 'middle');
      titleEn.setAttribute('fill', '#0F172A');
      titleEn.setAttribute('font-family', 'system-ui, sans-serif');
      titleEn.setAttribute('font-size', '12.5px');
      titleEn.setAttribute('font-weight', '700');
      titleEn.textContent = node.titleEn;
      g.appendChild(titleEn);

      // Arabic philosophical subtitle (below title)
      const titleAr = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      titleAr.setAttribute('x', node.x);
      titleAr.setAttribute('y', node.y + r + 36);
      titleAr.setAttribute('text-anchor', 'middle');
      titleAr.setAttribute('fill', '#334155');
      titleAr.setAttribute('font-family', 'system-ui, sans-serif');
      titleAr.setAttribute('font-size', '11.5px');
      titleAr.setAttribute('font-weight', '500');
      titleAr.textContent = node.titleAr;
      g.appendChild(titleAr);

      // Status Badge Pill (below subtitle)
      const badgeY = node.y + r + 50;
      const statusBadge = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      const badgeText = gateStatus;
      const badgeWidth = badgeText.length * 7 + 18;
      statusBadge.setAttribute('x', node.x - badgeWidth / 2);
      statusBadge.setAttribute('y', badgeY);
      statusBadge.setAttribute('width', badgeWidth);
      statusBadge.setAttribute('height', 18);
      statusBadge.setAttribute('rx', 4);

      let badgeFill = '#F1F5F9';
      let badgeStroke = '#E2E8F0';
      let badgeTextColor = '#64748B';

      if (gateStatus === 'PENDING') {
        badgeFill = '#FFFBEB';
        badgeStroke = '#FDE68A';
        badgeTextColor = '#92400E';
      } else if (gateStatus === 'ACTIVE') {
        badgeFill = '#EFF6FF';
        badgeStroke = '#BFDBFE';
        badgeTextColor = '#1E40AF';
      } else if (gateStatus === 'PASSED' || gateStatus === 'VERIFIED_PASSED') {
        badgeFill = '#ECFDF5';
        badgeStroke = '#A7F3D0';
        badgeTextColor = '#065F46';
      }

      statusBadge.setAttribute('fill', badgeFill);
      statusBadge.setAttribute('stroke', badgeStroke);
      statusBadge.setAttribute('stroke-width', '1');
      g.appendChild(statusBadge);

      const statusText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      statusText.setAttribute('x', node.x);
      statusText.setAttribute('y', badgeY + 13);
      statusText.setAttribute('text-anchor', 'middle');
      statusText.setAttribute('fill', badgeTextColor);
      statusText.setAttribute('font-family', 'ui-monospace, monospace');
      statusText.setAttribute('font-size', '10px');
      statusText.setAttribute('font-weight', '700');
      statusText.textContent = badgeText;
      g.appendChild(statusText);

      // Node interactive hover state
      g.addEventListener('mouseenter', () => {
        baseCircle.setAttribute('stroke-width', '3');
      });
      g.addEventListener('mouseleave', () => {
        baseCircle.setAttribute('stroke-width', isActive ? '3' : '2');
      });

      // Click handler
      g.addEventListener('click', () => {
        if (typeof this.options.onNodeClick === 'function') {
          this.options.onNodeClick(node.id);
        }
      });

      this.nodesGroup.appendChild(g);
    }
  }
}
