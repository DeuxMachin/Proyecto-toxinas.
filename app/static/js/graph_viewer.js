document.addEventListener("DOMContentLoaded", () => {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const propertiesContainer = document.querySelector('.graph-properties-container');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Update active button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            // Show/hide properties table based on active tab
            if (tabId === 'graph-view') {
                propertiesContainer.style.display = 'block';
                // Add class to body for CSS targeting if needed
                document.body.classList.add('graph-tab-active');
            } else {
                propertiesContainer.style.display = 'none';
                document.body.classList.remove('graph-tab-active');
            }
        });
    });
    
    // Initialize - hide table on page load since structure tab is default
    if (propertiesContainer) {
        propertiesContainer.style.display = 'none';
    }
    
    // Graph visualization functionality
    const graphPlotElement = document.getElementById('graph-plot');
    const longInput = document.getElementById('long-input');
    const distInput = document.getElementById('dist-input');
    const granularityToggle = document.getElementById('granularity-toggle'); // NEW
    const propertiesHeader = document.getElementById('properties-header');
    const propertiesValues = document.getElementById('properties-values');
    
    // Current protein info
    let currentProteinGroup = null;
    let currentProteinId = null;
    
    // Initialize empty graph
    Plotly.newPlot(graphPlotElement, [], {
        title: 'Seleccione una proteína para ver su grafo',
        height: 500,
        scene: {
            xaxis: { title: 'x' },
            yaxis: { title: 'y' },
            zaxis: { title: 'z' }
        }
    });
    
    // Event listeners for inputs
    longInput.addEventListener('change', updateGraphVisualization);
    distInput.addEventListener('change', updateGraphVisualization);
    granularityToggle.addEventListener('change', updateGraphVisualization); // NEW
    
    // Listen for protein selection changes
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
    
    // Initial values
    currentProteinGroup = groupSelect.value;
    setTimeout(() => {
        currentProteinId = proteinSelect.value;
    }, 300);
    
    async function updateGraphVisualization() {
        if (!currentProteinId) return;
        
        const longValue = longInput.value;
        const distValue = distInput.value;
        const granularity = granularityToggle.checked ? 'atom' : 'CA'; // NEW
        
        try {
            showLoading(graphPlotElement);
            
            // Request graph data from server with granularity parameter
            const response = await fetch(`/get_protein_graph/${currentProteinGroup}/${currentProteinId}?long=${longValue}&threshold=${distValue}&granularity=${granularity}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update graph visualization
            Plotly.react(graphPlotElement, data.plotData, data.layout);

            
            // Update properties table
            updatePropertiesTable(data.properties);
            
        } catch (error) {
            console.error("Error fetching graph data:", error);
            Plotly.react(graphPlotElement, [], {
                title: 'Error al cargar el grafo: ' + error.message,
                height: 500
            });
            clearPropertiesTable();
        } finally {
            hideLoading(graphPlotElement);
        }
    }
    
    function updatePropertiesTable(properties) {
        // Clear existing headers and values
        propertiesHeader.innerHTML = '';
        propertiesValues.innerHTML = '';
        
        // Add new headers and values
        Object.keys(properties).forEach(key => {
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            const th = document.createElement('th');
            th.textContent = formattedKey;
            propertiesHeader.appendChild(th);
            
            const td = document.createElement('td');
            
            // Format number values
            let value = properties[key];
            if (typeof value === 'number') {
                if (value < 0.01 && value !== 0) {
                    value = value.toExponential(2);
                } else {
                    value = value.toFixed(2);
                }
            } else if (value === null) {
                value = 'N/A';
            }
            
            td.textContent = value;
            propertiesValues.appendChild(td);
        });
    }
    
    function clearPropertiesTable() {
        propertiesHeader.innerHTML = '<th>No hay datos disponibles</th>';
        propertiesValues.innerHTML = '<td>-</td>';
    }
    
    function showLoading(element) {
        Plotly.react(element, [], {
            title: 'Cargando grafo...',
            height: 500
        });
    }
    
    function hideLoading(element) {
        // Nothing to do here, the graph update will overwrite the loading state
    }
});