/**
 * Kant Compiler Toolchain - Topological Pipeline Dependency Graph (DAG)
 * Interactive SVG visualization of Macro-Circles C0 through C6.
 */

export class TopologicalPipelineGraph {
  constructor(containerElement, options = {}) {
    this.container = typeof containerElement === 'string'
      ? document.querySelector(containerElement)
      : containerElement;

    this.options = Object.assign({
      width: 1200,
      height: 260,
      nodeRadius: 32,
      onNodeClick: null,
    }, options);

    this.activeCircleId = 'C0';
    this.state = null;
    this.viewBox = { x: 0, y: 0, width: 1200, height: 260 };
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };

    this.stages = [
      { id: 'C0', wave: 'Pre-Wave', titleEn: 'Epistemology & Toolchain', titleAr: 'التأسيس الإبستمولوجي' },
      { id: 'C1', wave: 'Wave 1', titleEn: 'Aesthetic & Spacetime AST', titleAr: 'الأستطيقا المجاوزة' },
      { id: 'C2', wave: 'Wave 2', titleEn: 'Analytic & KANT-IR', titleAr: 'التحليلياء وشيم IR' },
      { id: 'C3', wave: 'Wave 3', titleEn: 'Dialectic & Noumena', titleAr: 'الجدلياء والنومان' },
      { id: 'C4', wave: 'Wave 4', titleEn: 'Method, VM & JIT', titleAr: 'مبحث المنهج والمفسر' },
      { id: 'C5', wave: 'Wave 5', titleEn: 'Foundational Proofs', titleAr: 'براهين الجودة الأربعة' },
      { id: 'C6', wave: 'Wave 6', titleEn: 'Official v0.1 Release', titleAr: 'الإطلاق والتوزيع v0.1' },
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

    // Defs for gradients and markers
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <marker id="arrow-gold" markerWidth="10" markerHeight="10" refX="8" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#B8913F"/>
      </marker>
      <marker id="arrow-muted" markerWidth="10" markerHeight="10" refX="8" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#2D3A4B"/>
      </marker>
      <linearGradient id="node-active-grad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#D4AF37"/>
        <stop offset="100%" stop-color="#8C6A22"/>
      </linearGradient>
      <linearGradient id="node-pending-grad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#1B2432"/>
        <stop offset="100%" stop-color="#161D27"/>
      </linearGradient>
      <filter id="glow-gold" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="6" result="blur"/>
        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
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
      const zoomFactor = e.deltaY > 0 ? 1.1 : 0.9;
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
    this.viewBox = { x: 0, y: 0, width: 1200, height: 260 };
    this.updateViewBox();
  }

  render(state, activeCircleId) {
    this.state = state;
    this.activeCircleId = activeCircleId || 'C0';
    if (!this.svg) return;

    this.edgesGroup.innerHTML = '';
    this.nodesGroup.innerHTML = '';

    const count = this.stages.length;
    const startX = 90;
    const endX = 1110;
    const stepX = (endX - startX) / (count - 1);
    const centerY = 120;
    const r = this.options.nodeRadius;

    const nodePositions = this.stages.map((stage, i) => ({
      ...stage,
      x: startX + i * stepX,
      y: centerY
    }));

    // Draw directed edges
    for (let i = 0; i < nodePositions.length - 1; i++) {
      const from = nodePositions[i];
      const to = nodePositions[i + 1];
      const isPastActive = from.id === this.activeCircleId;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const startEdgeX = from.x + r + 4;
      const endEdgeX = to.x - r - 8;
      dPath(path, startEdgeX, from.y, endEdgeX, to.y);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', isPastActive ? '#B8913F' : '#2D3A4B');
      path.setAttribute('stroke-width', isPastActive ? '2.5' : '1.5');
      path.setAttribute('stroke-dasharray', isPastActive ? 'none' : '4 4');
      path.setAttribute('marker-end', isPastActive ? 'url(#arrow-gold)' : 'url(#arrow-muted)');
      this.edgesGroup.appendChild(path);
    }

    // Draw nodes
    for (const node of nodePositions) {
      const isActive = node.id === this.activeCircleId;
      const circleData = this.state && this.state.circles ? this.state.circles.find(c => c.id === node.id) : null;
      const gateStatus = circleData ? (circleData.gate_status || 'PENDING') : 'PENDING';

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', `dag-node ${isActive ? 'active' : ''}`);
      g.setAttribute('data-id', node.id);
      g.style.cursor = 'pointer';

      // Outer ring for active node
      if (isActive) {
        const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        ring.setAttribute('cx', node.x);
        ring.setAttribute('cy', node.y);
        ring.setAttribute('r', r + 6);
        ring.setAttribute('fill', 'none');
        ring.setAttribute('stroke', '#B8913F');
        ring.setAttribute('stroke-width', '2');
        ring.setAttribute('stroke-dasharray', '5 3');
        ring.setAttribute('filter', 'url(#glow-gold)');
        g.appendChild(ring);
      }

      // Base circle
      const baseCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      baseCircle.setAttribute('cx', node.x);
      baseCircle.setAttribute('cy', node.y);
      baseCircle.setAttribute('r', r);
      baseCircle.setAttribute('fill', isActive ? 'url(#node-active-grad)' : 'url(#node-pending-grad)');
      baseCircle.setAttribute('stroke', isActive ? '#D4AF37' : '#2D3A4B');
      baseCircle.setAttribute('stroke-width', isActive ? '3' : '1.5');
      g.appendChild(baseCircle);

      // Node label ID
      const textId = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      textId.setAttribute('x', node.x);
      textId.setAttribute('y', node.y + 5);
      textId.setAttribute('text-anchor', 'middle');
      textId.setAttribute('fill', isActive ? '#0F141C' : '#F0F4F8');
      textId.setAttribute('font-family', 'ui-monospace, monospace');
      textId.setAttribute('font-size', '14px');
      textId.setAttribute('font-weight', '800');
      textId.textContent = node.id;
      g.appendChild(textId);

      // Wave tag (above node)
      const waveText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      waveText.setAttribute('x', node.x);
      waveText.setAttribute('y', node.y - r - 12);
      waveText.setAttribute('text-anchor', 'middle');
      waveText.setAttribute('fill', isActive ? '#D4AF37' : '#8B949E');
      waveText.setAttribute('font-family', 'ui-sans-serif, system-ui, sans-serif');
      waveText.setAttribute('font-size', '11px');
      waveText.setAttribute('font-weight', '700');
      waveText.textContent = node.wave;
      g.appendChild(waveText);

      // Philosophical title (below node)
      const titleAr = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      titleAr.setAttribute('x', node.x);
      titleAr.setAttribute('y', node.y + r + 20);
      titleAr.setAttribute('text-anchor', 'middle');
      titleAr.setAttribute('fill', isActive ? '#F0F4F8' : '#8B949E');
      titleAr.setAttribute('font-family', 'ui-sans-serif, system-ui, sans-serif');
      titleAr.setAttribute('font-size', '12px');
      titleAr.setAttribute('font-weight', '600');
      titleAr.textContent = node.titleAr;
      g.appendChild(titleAr);

      // Status pill (below title)
      const statusText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      statusText.setAttribute('x', node.x);
      statusText.setAttribute('y', node.y + r + 38);
      statusText.setAttribute('text-anchor', 'middle');
      statusText.setAttribute('fill', gateStatus === 'PASSED' ? '#2EA043' : (isActive ? '#38BDF8' : '#64748B'));
      statusText.setAttribute('font-family', 'ui-monospace, monospace');
      statusText.setAttribute('font-size', '10px');
      statusText.setAttribute('font-weight', '700');
      statusText.textContent = `[${gateStatus}]`;
      g.appendChild(statusText);

      // Click handler
      g.addEventListener('click', () => {
        if (typeof this.options.onNodeClick === 'function') {
          this.options.onNodeClick(node.id);
        }
      });

      this.nodesGroup.appendChild(g);
    }

    function dPath(elem, x1, y1, x2, y2) {
      elem.setAttribute('d', `M ${x1} ${y1} L ${x2} ${y2}`);
    }
  }
}
