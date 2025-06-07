document.addEventListener("DOMContentLoaded", async () => {
    
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const propertiesContainer = document.querySelector('.graph-properties-container');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            if (tabId === 'graph-view') {
                propertiesContainer.style.display = 'block';
                document.body.classList.add('graph-tab-active');

                if (window.molstarAnalyzer) {
                    analyzeMolstarStructure();
                }
            } else {
                propertiesContainer.style.display = 'none';
                document.body.classList.remove('graph-tab-active');
            }
        });
    });

    // Inicializar la primera pestaña como activa
    if (propertiesContainer) {
        propertiesContainer.style.display = 'none';
    }
    
    const graphPlotElement = document.getElementById('graph-plot');
    const longInput = document.getElementById('long-input');
    const distInput = document.getElementById('dist-input');
    const granularityToggle = document.getElementById('granularity-toggle');
    
    let currentProteinGroup = null;
    let currentProteinId = null;
    
    // Inicializamos el grafico vacio con plotly
    Plotly.newPlot(graphPlotElement, [], {
        title: 'Seleccione una proteína para ver su grafo',
        height: 500,
        scene: {
            xaxis: { title: 'x' },
            yaxis: { title: 'y' },
            zaxis: { title: 'z' }
        }
    });
    
    // Eventos para actualizar automaticamente el grafo
    longInput.addEventListener('change', updateGraphVisualization);
    distInput.addEventListener('change', updateGraphVisualization);
    granularityToggle.addEventListener('change', updateGraphVisualization);
    
    const groupSelect = document.getElementById('groupSelect');
    const proteinSelect = document.getElementById('proteinSelect');
    
    groupSelect.addEventListener('change', () => {
        currentProteinGroup = groupSelect.value;
        setTimeout(() => {
            currentProteinId = proteinSelect.value;
            updateGraphVisualization();
        }, 300);
    });
    
    proteinSelect.addEventListener('change', () => {
        currentProteinGroup = groupSelect.value;
        currentProteinId = proteinSelect.value;
        updateGraphVisualization();
    });
    
    currentProteinGroup = groupSelect.value;
    
    // Esperamos a que los selectores estén llenos
    setTimeout(async () => {
        currentProteinId = proteinSelect.value;
        
        // Inicializar grafo automáticamente si tenemos una proteína seleccionada
        if (currentProteinGroup && currentProteinId) {
            await updateGraphVisualization();
        }
    }, 800);
    
    // Función para actualizar la visualización del grafo
    async function updateGraphVisualization() {
        if (!currentProteinGroup || !currentProteinId) {
            clearAnalysisPanel();
            return;
        }

        try {
            const longValue = longInput.value;
            const distValue = distInput.value;
            const granularity = granularityToggle.checked ? 'atom' : 'CA';
            
            showLoading(graphPlotElement);
            
            const response = await fetch(`/get_protein_graph/${currentProteinGroup}/${currentProteinId}?long=${longValue}&threshold=${distValue}&granularity=${granularity}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                clearAnalysisPanel();
                return;
            }

            Plotly.react(graphPlotElement, data.plotData, data.layout);
            
            updateBasicStructuralInfo(data.properties, granularity);
            updateAdvancedMetrics(data); 
            analyzeMolstarStructure();

        } catch (error) {
            clearAnalysisPanel();
            Plotly.react(graphPlotElement, [], {
                title: 'Error al cargar el grafo: ' + error.message,
                height: 500
            });
        } finally {
            hideLoading(graphPlotElement);
        }
    }
    
    function updateBasicStructuralInfo(properties, granularity) {
        if (!properties) return;
        
        const toxinName = `${currentProteinGroup.toUpperCase()}_${currentProteinId}`;
        updateElementText('toxin-name', toxinName);
        
        // Actualizar datos básicos del grafo
        updateElementText('num-nodes', properties.num_nodes || '-');
        updateElementText('num-edges', properties.num_edges || '-');
        
        // Densidad del grafo
        updateElementText('graph-density', (properties.density || 0).toFixed(4));
        
        // Coeficiente de agrupamiento
        updateElementText('avg-clustering', (properties.avg_clustering || 0).toFixed(4));
        
        // Mostrar tipo de grafo (átomo o CA)
        const granularityText = granularity === 'atom' ? 'Nivel atómico' : 'Nivel de residuos (CA)';
        
        const infoElement = document.getElementById('graph-info');
        if (infoElement) {
            infoElement.textContent = `Grafo visualizado en: ${granularityText}`;
        }
    }

    async function analyzeMolstarStructure() {
        try {
            if (!window.molstarAnalyzer) {
                return;
            }
            
            const analysis = await window.molstarAnalyzer.analyzeCurrentStructure();
            
            if (analysis) {
                // Actualizar datos complementarios y métricas avanzadas
                updateAdvancedMetrics(analysis);
                
                // Actualizar puentes disulfuro si no se actualizaron antes
                const disulfideBridgesElement = document.getElementById('disulfide-bridges');
                if (disulfideBridgesElement && disulfideBridgesElement.textContent === '-') {
                    updateElementText('disulfide-bridges', analysis.graph_properties?.disulfide_bridges || '0');
                }
            }
        } catch (error) {
            // No mostramos el error para mantener la interfaz limpia
        }
    }
    
    function updateAdvancedMetrics(analysis) {
        // Métricas de centralidad 
        const metrics = analysis.summary_statistics;
        if (metrics) {
            // Degree Centrality
            updateElementText('degree-min', metrics.degree_centrality?.min?.toFixed(4) || '-');
            updateElementText('degree-max', metrics.degree_centrality?.max?.toFixed(4) || '-');
            updateElementText('degree-mean', metrics.degree_centrality?.mean?.toFixed(4) || '-');
            updateElementText('degree-top', metrics.degree_centrality?.top_residues || '-');

            // Betweenness Centrality
            updateElementText('between-min', metrics.betweenness_centrality?.min?.toFixed(4) || '-');
            updateElementText('between-max', metrics.betweenness_centrality?.max?.toFixed(4) || '-');
            updateElementText('between-mean', metrics.betweenness_centrality?.mean?.toFixed(4) || '-');
            updateElementText('between-top', metrics.betweenness_centrality?.top_residues || '-');

            // Closeness Centrality
            updateElementText('closeness-min', metrics.closeness_centrality?.min?.toFixed(4) || '-');
            updateElementText('closeness-max', metrics.closeness_centrality?.max?.toFixed(4) || '-');
            updateElementText('closeness-mean', metrics.closeness_centrality?.mean?.toFixed(4) || '-');
            updateElementText('closeness-top', metrics.closeness_centrality?.top_residues || '-');

            // Clustering Coefficient
            updateElementText('clustering-min', metrics.clustering_coefficient?.min?.toFixed(4) || '-');
            updateElementText('clustering-max', metrics.clustering_coefficient?.max?.toFixed(4) || '-');
            updateElementText('clustering-mean', metrics.clustering_coefficient?.mean?.toFixed(4) || '-');
            updateElementText('clustering-top', metrics.clustering_coefficient?.top_residues || '-');
        }

        // Top 5 residuos
        const top5 = analysis.top_5_residues;
        if (top5) {
            populateTop5List('top-degree-list', top5.degree_centrality);
            populateTop5List('top-between-list', top5.betweenness_centrality);
            populateTop5List('top-closeness-list', top5.closeness_centrality);
            populateTop5List('top-clustering-list', top5.clustering_coefficient);
        }
    }

    function showLoading(element) {
        Plotly.react(element, [], {
            title: 'Cargando grafo...',
            height: 500
        });
    }
    
    function hideLoading(element) {
        // Función vacía por ahora
    }

    // Configurar botón de exportación 
    function setupExportButton() {
        const exportBtn = document.getElementById('export-csv-btn');
        const familySelector = document.getElementById('family-selector');
        const exportFamilyBtn = document.getElementById('export-family-csv-btn');
        
        if (!exportBtn) return;
        
        const buttonText = exportBtn.querySelector('.button-text');
        const loadingText = exportBtn.querySelector('.loading-text');
        
        // Exportación individual (código actualizado)
        exportBtn.addEventListener('click', async () => {
            if (!currentProteinGroup || !currentProteinId) {
                alert('Por favor seleccione una toxina primero');
                return;
            }
            
            exportBtn.disabled = true;
            buttonText.style.display = 'none';
            loadingText.style.display = 'inline';
            
            try {
                const longValue = longInput.value;
                const distValue = distInput.value;
                const granularity = granularityToggle.checked ? 'atom' : 'CA';
                
                const nameResponse = await fetch(`/get_toxin_name/${currentProteinGroup}/${currentProteinId}`);
                const nameData = await nameResponse.json();
                const toxinName = nameData.toxin_name || `${currentProteinGroup}_${currentProteinId}`;
                
                const cleanName = toxinName.replace(/[^\w\-_]/g, '');
                
                let filename;
                if (currentProteinGroup === "nav1_7") {
                    filename = `Nav1.7-${cleanName}.csv`;
                } else {
                    filename = `Toxinas-${cleanName}.csv`;
                }
                
                const url = `/export_residues_csv/${currentProteinGroup}/${currentProteinId}?long=${longValue}&threshold=${distValue}&granularity=${granularity}`;
                
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
            } catch (error) {
                alert('Error al generar el archivo CSV: ' + error.message);
            } finally {
                setTimeout(() => {
                    exportBtn.disabled = false;
                    buttonText.style.display = 'inline';
                    loadingText.style.display = 'none';
                }, 2000);
            }
        });
        
        // Habilitar/deshabilitar botón de familia basado en selección
        if (familySelector && exportFamilyBtn) {
            familySelector.addEventListener('change', () => {
                exportFamilyBtn.disabled = !familySelector.value;
            });
            
            // Exportación por familias 
            exportFamilyBtn.addEventListener('click', async () => {
                const selectedFamily = familySelector.value;
                if (!selectedFamily) {
                    alert('Por favor seleccione una familia de toxinas');
                    return;
                }
                
                const familyButtonText = exportFamilyBtn.querySelector('.button-text');
                const familyLoadingText = exportFamilyBtn.querySelector('.loading-text');
                
                exportFamilyBtn.disabled = true;
                familyButtonText.style.display = 'none';
                familyLoadingText.style.display = 'inline';
                
                try {
                    const longValue = longInput.value;
                    const distValue = distInput.value;
                    const granularity = granularityToggle.checked ? 'atom' : 'CA';
                    
                    // Mapeo de familias mejorado
                    const familyNames = {
                        'μ-TRTX-H': 'Mu_TRTX_H_terminacion_2a',
                        'μ-TRTX-C': 'Mu_TRTX_C_terminacion_2b',
                        'β-TRTX': 'Beta_TRTX',
                        'ω-TRTX': 'Omega_TRTX',
                        'δ-TRTX': 'Delta_TRTX'
                    };
                    
                    const familyName = familyNames[selectedFamily] || selectedFamily.replace(/[^\w]/g, '_');
                    const filename = `Dataset_${familyName}_IC50_Topologia_${granularity}.csv`;
                    
                    const url = `/export_family_csv/${encodeURIComponent(selectedFamily)}?long=${longValue}&threshold=${distValue}&granularity=${granularity}`;
                    
                    console.log('🚀 Descargando familia:', selectedFamily);
                    console.log('📁 URL:', url);
                    
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // Mostrar mensaje informativo
                    setTimeout(() => {
                        alert(`¡Dataset de ${selectedFamily} generado exitosamente!\n\nEl archivo contiene:\n• Métricas topológicas completas\n• Valores IC₅₀ normalizados\n• Subfamilias correctamente diferenciadas\n• Datos ordenados por toxina y posición\n\nPerfecto para análisis estructura-actividad.`);
                    }, 1000);
                    
                } catch (error) {
                    console.error('❌ Error:', error);
                    alert('Error al generar el dataset familiar: ' + error.message);
                } finally {
                    setTimeout(() => {
                        exportFamilyBtn.disabled = familySelector.value === '';
                        familyButtonText.style.display = 'inline';
                        familyLoadingText.style.display = 'none';
                    }, 4000); // Más tiempo para procesamiento de familias
                }
            });
        }
    }
    // Llamar setupExportButton DENTRO del scope donde están definidas las variables
    setupExportButton();

    // Exponer funciones globalmente
    window.updateGraphVisualization = updateGraphVisualization;
    window.analyzeMolstarStructure = analyzeMolstarStructure;
    window.currentProteinGroup = () => currentProteinGroup;
    window.currentProteinId = () => currentProteinId;
    window.setCurrentProtein = (group, id) => {
        currentProteinGroup = group;
        currentProteinId = id;
    };
});

// Función para ser llamada desde la gestión de pestañas
window.triggerGraphUpdate = function(group, id) {
    if (group && id && window.setCurrentProtein) {
        window.setCurrentProtein(group, id);
        window.updateGraphVisualization();
    }
};

// Funciones auxiliares fuera del scope principal
function updateAnalysisPanel(analysisData) {
    if (!analysisData) {
        return;
    }
    
    const nodesElement = document.getElementById('num-nodes');
    if (nodesElement && nodesElement.textContent === '-') {
        updateElementText('toxin-name', analysisData.toxin || '-');
        updateElementText('num-nodes', analysisData.graph_properties?.nodes || '-');
        updateElementText('num-edges', analysisData.graph_properties?.edges || '-');
        updateElementText('disulfide-bridges', analysisData.graph_properties?.disulfide_bridges || '-');
        updateElementText('graph-density', (analysisData.graph_properties?.density || 0).toFixed(4));
        updateElementText('avg-clustering', (analysisData.graph_properties?.clustering_coefficient_avg || 0).toFixed(4));
    }
}

function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

function populateTop5List(listId, items) {
    const list = document.getElementById(listId);
    if (!list) return;
    
    list.innerHTML = '';
    
    if (!items || items.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No hay datos disponibles';
        list.appendChild(li);
        return;
    }
    
    items.forEach((item, index) => {
        const li = document.createElement('li');
        // Verificar si tenemos la información completa del residuo
        if (item.residueName && item.chain) {
            // Formato deseado: "VAL21 (Cadena A): 0.1122"
            li.textContent = `${item.residueName}${item.residue} (Cadena ${item.chain}): ${item.value.toFixed(4)}`;
        } else {
            // Fallback al formato anterior si no tenemos toda la información
            li.textContent = `${item.residueName}${item.residue}: ${item.value.toFixed(4)}`;
        }
        list.appendChild(li);
    });
}

function clearAnalysisPanel() {
    // Función para limpiar el panel de análisis
}


