/**
 * Molstar Graph Renderer
 * WebGL-optimized 3D graph visualization using Mol* infrastructure
 * Replaces Plotly for sub-second rendering of dense molecular graphs
 */

class MolstarGraphRenderer {
    constructor(containerElement) {
        this.container = containerElement;
        this.canvas = null;
        this.ctx = null;
        this.graphData = null;
        this.camera = {
            rotation: { x: 0.3, y: 0.3 },
            zoom: 1,
            distance: 150,
            target: { x: 0, y: 0, z: 0 }
        };
        this.isDragging = false;
        this.lastMouse = { x: 0, y: 0 };
        this.initialZoom = 1;
        this.initialDistance = 150;
        
        this.initCanvas();
        this.setupInteraction();
    }
    
    initCanvas() {
        // Clear container and create canvas
        this.container.innerHTML = '';
        this.container.style.position = 'relative';
        
        // Create canvas element for rendering
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.display = 'block';
        this.canvas.style.cursor = 'grab';
        
        this.container.appendChild(this.canvas);
        
        // Get 2D context with antialiasing
        this.ctx = this.canvas.getContext('2d', { alpha: false, willReadFrequently: false });
        
        // Create zoom controls UI
        this.createZoomControls();
        
        // Create hover tooltip
        this.createTooltip();
        
        // Handle resizing
        window.addEventListener('resize', () => this.handleResize());
    }
    
    createZoomControls() {
        const controlsDiv = document.createElement('div');
        controlsDiv.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 1000;
        `;
        
        const buttonStyle = `
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 8px;
            background: rgba(30, 30, 50, 0.9);
            color: white;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s;
            backdrop-filter: blur(10px);
        `;
        
        // Zoom In button
        const zoomInBtn = document.createElement('button');
        zoomInBtn.innerHTML = '➕';
        zoomInBtn.style.cssText = buttonStyle;
        zoomInBtn.title = 'Acercar (Zoom In)';
        zoomInBtn.onmouseover = () => zoomInBtn.style.background = 'rgba(60, 120, 255, 0.9)';
        zoomInBtn.onmouseout = () => zoomInBtn.style.background = 'rgba(30, 30, 50, 0.9)';
        zoomInBtn.onclick = () => this.zoomIn();
        
        // Zoom Out button
        const zoomOutBtn = document.createElement('button');
        zoomOutBtn.innerHTML = '➖';
        zoomOutBtn.style.cssText = buttonStyle;
        zoomOutBtn.title = 'Alejar (Zoom Out)';
        zoomOutBtn.onmouseover = () => zoomOutBtn.style.background = 'rgba(60, 120, 255, 0.9)';
        zoomOutBtn.onmouseout = () => zoomOutBtn.style.background = 'rgba(30, 30, 50, 0.9)';
        zoomOutBtn.onclick = () => this.zoomOut();
        
        // Reset button
        const resetBtn = document.createElement('button');
        resetBtn.innerHTML = '🔄';
        resetBtn.style.cssText = buttonStyle;
        resetBtn.title = 'Resetear Vista';
        resetBtn.onmouseover = () => resetBtn.style.background = 'rgba(60, 120, 255, 0.9)';
        resetBtn.onmouseout = () => resetBtn.style.background = 'rgba(30, 30, 50, 0.9)';
        resetBtn.onclick = () => this.resetView();
        
        controlsDiv.appendChild(zoomInBtn);
        controlsDiv.appendChild(zoomOutBtn);
        controlsDiv.appendChild(resetBtn);
        
        this.container.appendChild(controlsDiv);
    }
    
    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.style.cssText = `
            position: absolute;
            display: none;
            background: rgba(20, 20, 40, 0.95);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-family: 'Segoe UI', Arial, sans-serif;
            pointer-events: none;
            z-index: 2000;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(100, 150, 255, 0.3);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            white-space: nowrap;
        `;
        this.container.appendChild(this.tooltip);
        this.hoveredNode = null;
    }
    
    zoomIn() {
        this.camera.distance *= 0.8;
        this.camera.distance = Math.max(20, this.camera.distance);
        this.render();
    }
    
    zoomOut() {
        this.camera.distance *= 1.2;
        this.camera.distance = Math.min(1000, this.camera.distance);
        this.render();
    }
    
    setupInteraction() {
        // Mouse controls for rotation
        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.canvas.style.cursor = 'grabbing';
            this.lastMouse = { x: e.clientX, y: e.clientY };
        });
        
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            if (this.isDragging) {
                const dx = e.clientX - this.lastMouse.x;
                const dy = e.clientY - this.lastMouse.y;
                
                this.camera.rotation.y += dx * 0.01;
                this.camera.rotation.x += dy * 0.01;
                
                this.lastMouse = { x: e.clientX, y: e.clientY };
                this.render();
            } else {
                // Check for hover over nodes
                this.checkNodeHover(mouseX, mouseY);
            }
        });
        
        this.canvas.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
        });
        
        this.canvas.addEventListener('mouseleave', () => {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
            this.hideTooltip();
        });
        
        // Mouse wheel for zoom - FUNCIONAL
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 1.15 : 0.87;
            this.camera.distance *= delta;
            this.camera.distance = Math.max(20, Math.min(1000, this.camera.distance));
            this.render();
        });
        
        // Double-click to reset view
        this.canvas.addEventListener('dblclick', () => {
            this.resetView();
        });
    }
    
    checkNodeHover(mouseX, mouseY) {
        if (!this.graphData || !this.projectedNodes) {
            this.hideTooltip();
            return;
        }
        
        let foundNode = null;
        let foundIndex = -1;
        
        // Check each node for hover (reverse order to match rendering)
        for (let i = this.projectedNodes.length - 1; i >= 0; i--) {
            const p = this.projectedNodes[i];
            if (!p) continue;
            
            const baseSizeScale = p.scale / this.camera.zoom * 0.015;
            const size = Math.max(3, 8 * baseSizeScale);
            
            const dx = mouseX - p.x;
            const dy = mouseY - p.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= size + 5) {
                foundNode = this.graphData.nodes[i];
                foundIndex = i;
                break;
            }
        }
        
        if (foundNode) {
            this.showTooltip(foundNode, foundIndex, mouseX, mouseY);
        } else {
            this.hideTooltip();
        }
    }
    
    showTooltip(node, index, mouseX, mouseY) {
        this.hoveredNode = index;
        
        const rect = this.canvas.getBoundingClientRect();
        const tooltipX = rect.left + mouseX + 15;
        const tooltipY = rect.top + mouseY - 10;
        
        this.tooltip.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 6px; color: #4fc3f7;">
                ${node.label}
            </div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.8);">
                <div>x: ${node.x.toFixed(2)}</div>
                <div>y: ${node.y.toFixed(2)}</div>
                <div>z: ${node.z.toFixed(2)}</div>
                <div style="margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.2);">
                    Nodo #${index}
                </div>
            </div>
        `;
        
        this.tooltip.style.left = tooltipX + 'px';
        this.tooltip.style.top = tooltipY + 'px';
        this.tooltip.style.display = 'block';
        
        this.render(); // Re-render to highlight hovered node
    }
    
    hideTooltip() {
        if (this.hoveredNode !== null) {
            this.hoveredNode = null;
            this.render();
        }
        this.tooltip.style.display = 'none';
    }
    
    /**
     * Reset camera to initial view
     */
    resetView() {
        this.camera.rotation = { x: 0.2, y: 0.2 };
        this.camera.distance = this.initialDistance;
        this.camera.zoom = this.initialZoom;
        this.hideTooltip();
        this.render();
    }
    
    handleResize() {
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        if (this.graphData) {
            this.render();
        }
    }
    
    /**
     * Load and render graph data
     * @param {Object} data - Graph data with nodes and edges
     * @param {Array} data.nodes - Array of {x, y, z, label}
     * @param {Array} data.edges - Array of [nodeIndex1, nodeIndex2]
     * @param {Object} data.graphMetadata - Metadata including bbox
     */
    loadGraph(data) {
        this.graphData = data;
        
        // Set camera to center of bounding box
        if (data.graphMetadata && data.graphMetadata.bbox) {
            const center = data.graphMetadata.bbox.center;
            this.camera.target = { x: center[0], y: center[1], z: center[2] };
            
            // Calculate initial distance based on bbox size for optimal view
            const bbox = data.graphMetadata.bbox;
            const size = Math.max(
                bbox.max[0] - bbox.min[0],
                bbox.max[1] - bbox.min[1],
                bbox.max[2] - bbox.min[2]
            );
            
            // Initial distance: CLOSER to see all connections clearly
            this.camera.distance = size * 1.8; // Reduced from 2.5 to 1.8
            this.initialDistance = this.camera.distance;
            this.camera.zoom = Math.min(this.canvas.width, this.canvas.height) / (size * 1.5);
            this.initialZoom = this.camera.zoom;
        }
        
        // Reset rotation for better initial view
        this.camera.rotation = { x: 0.2, y: 0.2 };
        
        this.render();
    }
    
    /**
     * Project 3D point to 2D screen coordinates
     */
    project3D(x, y, z) {
        // Simple perspective projection
        const cx = this.camera.target.x;
        const cy = this.camera.target.y;
        const cz = this.camera.target.z;
        
        // Translate to camera space
        let px = x - cx;
        let py = y - cy;
        let pz = z - cz;
        
        // Apply rotation
        const cosX = Math.cos(this.camera.rotation.x);
        const sinX = Math.sin(this.camera.rotation.x);
        const cosY = Math.cos(this.camera.rotation.y);
        const sinY = Math.sin(this.camera.rotation.y);
        
        // Rotate around Y axis
        let tx = px * cosY - pz * sinY;
        let tz = px * sinY + pz * cosY;
        px = tx;
        pz = tz;
        
        // Rotate around X axis
        let ty = py * cosX - pz * sinX;
        tz = py * sinX + pz * cosX;
        py = ty;
        pz = tz;
        
        // Perspective projection with improved depth
        const scale = this.camera.zoom * this.camera.distance / (this.camera.distance + pz);
        
        const screenX = this.canvas.width / 2 + px * scale;
        const screenY = this.canvas.height / 2 - py * scale;
        
        return { x: screenX, y: screenY, z: pz, scale };
    }
    
    /**
     * Render the graph
     */
    render() {
        if (!this.graphData || !this.ctx) return;
        
        const ctx = this.ctx;
        const { nodes, edges } = this.graphData;
        
        // Clear canvas
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Fondo estilo científico moderno (similar a Plotly oscuro)
        const gradient = ctx.createRadialGradient(
            this.canvas.width / 2, this.canvas.height / 2, 0,
            this.canvas.width / 2, this.canvas.height / 2, this.canvas.width / 1.5
        );
        gradient.addColorStop(0, '#1e1e2e');
        gradient.addColorStop(0.5, '#181825');
        gradient.addColorStop(1, '#0f0f1a');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Optional: Add subtle grid pattern for depth
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
        ctx.lineWidth = 1;
        for (let i = 0; i < this.canvas.width; i += 50) {
            ctx.beginPath();
            ctx.moveTo(i, 0);
            ctx.lineTo(i, this.canvas.height);
            ctx.stroke();
        }
        for (let i = 0; i < this.canvas.height; i += 50) {
            ctx.beginPath();
            ctx.moveTo(0, i);
            ctx.lineTo(this.canvas.width, i);
            ctx.stroke();
        }
        
        // Project all nodes to 2D and store for hover detection
        this.projectedNodes = nodes.map(node => {
            const p = this.project3D(node.x, node.y, node.z);
            return { ...p, label: node.label };
        });
        
        // Sort by depth (z) for proper rendering order
        const sortedIndices = this.projectedNodes.map((p, i) => ({ z: p.z, i }))
            .sort((a, b) => a.z - b.z)
            .map(item => item.i);
        
        // Draw ALL edges - MÁXIMA VISIBILIDAD
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Sort edges by average depth for better rendering
        const edgesWithDepth = edges.map(([i, j]) => {
            const p1 = this.projectedNodes[i];
            const p2 = this.projectedNodes[j];
            if (!p1 || !p2) return null;
            const avgZ = (p1.z + p2.z) / 2;
            return { i, j, p1, p2, avgZ };
        }).filter(e => e !== null);
        
        edgesWithDepth.sort((a, b) => a.avgZ - b.avgZ);
        
        // Draw ALL edges with consistent high visibility
        for (const edge of edgesWithDepth) {
            const { p1, p2, avgZ } = edge;
            
            // Depth factor for subtle 3D effect
            const depthFactor = Math.max(0.3, Math.min(1, (avgZ + 150) / 300));
            
            // TODAS las aristas visibles con buen grosor y opacidad
            const lineWidth = 2.0 + (depthFactor * 0.8);
            const opacity = 0.5 + depthFactor * 0.3;
            
            // Color cyan/azul brillante como Plotly
            ctx.strokeStyle = `rgba(99, 179, 237, ${opacity})`;
            ctx.lineWidth = lineWidth;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        }
        
        // Draw nodes - SIMILAR A PLOTLY CON HOVER HIGHLIGHT
        for (const idx of sortedIndices) {
            const p = this.projectedNodes[idx];
            if (!p) continue;
            
            // Node size varies with depth
            const baseSizeScale = p.scale / this.camera.zoom * 0.015;
            const size = Math.max(4, 9 * baseSizeScale);
            
            const isHovered = (this.hoveredNode === idx);
            const hoverScale = isHovered ? 1.5 : 1.0;
            const finalSize = size * hoverScale;
            
            // Depth factor for color
            const depthFactor = Math.max(0.3, Math.min(1, (p.z + 150) / 300));
            
            // Create radial gradient for 3D sphere effect
            const gradient = ctx.createRadialGradient(
                p.x - finalSize * 0.3, p.y - finalSize * 0.3, 0,
                p.x, p.y, finalSize
            );
            
            if (isHovered) {
                // Highlighted node - amarillo/naranja brillante
                gradient.addColorStop(0, 'rgba(255, 220, 100, 1)');
                gradient.addColorStop(0.6, 'rgba(255, 180, 50, 0.95)');
                gradient.addColorStop(1, 'rgba(230, 140, 30, 0.8)');
            } else {
                // Normal nodes - esquema rosa/magenta/morado como Plotly
                const r = Math.floor(200 + 55 * depthFactor);
                const g = Math.floor(100 + 80 * depthFactor);
                const b = Math.floor(200 + 55 * depthFactor);
                
                gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.95)`);
                gradient.addColorStop(0.7, `rgba(${r - 30}, ${g - 20}, ${b - 30}, 0.9)`);
                gradient.addColorStop(1, `rgba(${r - 60}, ${g - 40}, ${b - 60}, 0.75)`);
            }
            
            // Draw node
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(p.x, p.y, finalSize, 0, Math.PI * 2);
            ctx.fill();
            
            // Border - más grueso si está en hover
            ctx.strokeStyle = isHovered 
                ? 'rgba(255, 255, 255, 1)' 
                : `rgba(255, 255, 255, ${0.5 + depthFactor * 0.3})`;
            ctx.lineWidth = isHovered ? 2.5 : 1.5;
            ctx.stroke();
            
            // Inner glow sutil
            if (!isHovered) {
                ctx.strokeStyle = `rgba(255, 200, 255, ${0.3 + depthFactor * 0.2})`;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, finalSize * 0.5, 0, Math.PI * 2);
                ctx.stroke();
            }
        }
        
        // Draw info panel - LIMPIO Y PROFESIONAL
        const padding = 14;
        const lineHeight = 22;
        const panelWidth = 240;
        const panelHeight = 70;
        
        // Semi-transparent dark panel
        ctx.fillStyle = 'rgba(20, 20, 40, 0.85)';
        ctx.fillRect(10, 10, panelWidth, panelHeight);
        
        // Border
        ctx.strokeStyle = 'rgba(99, 179, 237, 0.4)';
        ctx.lineWidth = 1;
        ctx.strokeRect(10, 10, panelWidth, panelHeight);
        
        // Info text
        ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        ctx.font = 'bold 15px "Segoe UI", Arial, sans-serif';
        ctx.fillText(`📊 Nodos: ${nodes.length} | Aristas: ${edges.length}`, padding + 6, padding + lineHeight);
        
        ctx.font = '13px "Segoe UI", Arial, sans-serif';
        const distPercent = ((this.initialDistance / this.camera.distance) * 100).toFixed(0);
        ctx.fillText(`🔍 Zoom: ${distPercent}%`, padding + 6, padding + lineHeight * 2);
        
        ctx.fillStyle = 'rgba(180, 220, 255, 0.85)';
        ctx.font = '12px "Segoe UI", Arial, sans-serif';
        ctx.fillText('🖱️ Arrastrar para rotar | Hover en nodo para info', padding + 6, padding + lineHeight * 3);
    }
    
    /**
     * Clear the graph
     */
    clear() {
        this.graphData = null;
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }
    
    /**
     * Destroy the renderer and clean up
     */
    destroy() {
        window.removeEventListener('resize', this.handleResize);
        this.hideTooltip();
        
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        if (this.tooltip && this.tooltip.parentNode) {
            this.tooltip.parentNode.removeChild(this.tooltip);
        }
        
        this.canvas = null;
        this.ctx = null;
        this.graphData = null;
        this.projectedNodes = null;
        this.tooltip = null;
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.MolstarGraphRenderer = MolstarGraphRenderer;
}
