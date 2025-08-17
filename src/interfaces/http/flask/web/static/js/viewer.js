document.addEventListener("DOMContentLoaded", async () => {
    //Extremos los datos de la proteina 
    const proteinData = JSON.parse(document.getElementById("protein-data").textContent);
    
    const toxinasData = proteinData.toxinas;
    const navsData = proteinData.nav1_7;

    const viewerElement = document.getElementById("viewer");

    
    const plugin = await molstar.Viewer.create(viewerElement, {
        layoutIsExpanded: false,
        layoutShowControls: false,
        layoutShowRemoteState: false,
        layoutShowSequence: true,
        layoutShowLog: false,
        layoutShowLeftPanel: true,
        viewportShowExpand: false,
        viewportShowSelectionMode: false,
        viewportShowAnimation: false
    });

    // Creamos un analizador de proteínas mediante Molstar
    window.molstarAnalyzer = new MolstarProteinAnalyzer(plugin);

    const groupSelect = document.getElementById("groupSelect");
    const proteinSelect = document.getElementById("proteinSelect");

    function loadProteins(group) {
        const list = group === "toxinas" ? toxinasData : navsData;
        proteinSelect.innerHTML = "";

        if (!list || list.length === 0) return;

        list.forEach(([id, name]) => {
            const opt = document.createElement("option");
            opt.value = id;
            opt.textContent = name;
            proteinSelect.appendChild(opt);
        });
        
        // Selecciona automáticamente la primera opción
        if (proteinSelect.options.length > 0) {
            proteinSelect.selectedIndex = 0;
        }
    }

    async function loadPDB(group, id) {
        try {
            // Limpiar el plugin antes de cargar una nueva estructura
            try {
                await plugin.plugin?.clear?.();
                await plugin.resetCamera?.();
                await plugin.resetStructure?.();
            } catch (clearError) {
                // Ignorar errores al limpiar
            }

            // Obtener los datos PDB del servidor usando únicamente la ruta v2
            const res = await fetch(`/v2/structures/${group}/${id}/pdb`);
            if (!res.ok) {
                throw new Error(`Error HTTP: ${res.status}`);
            }
            
            const pdbText = await res.text();
            if (!pdbText || !pdbText.includes("ATOM")) {
                throw new Error("PDB inválido o vacío");
            }

            // Crear un blob tempoal para que Molstar pueda cargarlo en lugar de usar un URL directo
            const blob = new Blob([pdbText], { type: 'chemical/x-pdb' });
            const blobUrl = URL.createObjectURL(blob);
            
            try {
                // Cargar la estructura usando el método correcto 
                await plugin.loadStructureFromUrl(blobUrl, 'pdb');
                
                
                const graphTab = document.querySelector('[data-tab="graph-view"]');
                if (graphTab && graphTab.classList.contains('active')) {
                    setTimeout(() => {
                        if (window.analyzeMolstarStructure) {
                            window.analyzeMolstarStructure();
                        }
                    }, 1000); // Dar tiempo a que la estructura se cargue completamente
                }
                
            } finally {
                // Liberar el URL del blob esto para evitar fugas de memoria
                URL.revokeObjectURL(blobUrl);
            }
        } catch (error) {
            alert("Error al cargar la estructura: " + error.message);
        }
    }

    // Variables para manejo de dipolo
    let currentDipoleData = null;
    let dipoleCalculationInProgress = false;

    // Cuando cambiemos el grupo de proteínas, cargamos las proteínas correspondientes
    groupSelect.addEventListener("change", () => {
        const group = groupSelect.value;
        loadProteins(group);
        
        const selectedId = proteinSelect.value;
        if (selectedId) {
            loadPDB(group, selectedId);
            // Notify dual view manager
            if (window.dualViewManager) {
                const selectedName = proteinSelect.options[proteinSelect.selectedIndex]?.text;
                window.dualViewManager.onDatabaseProteinSelected(group, selectedId, selectedName);
            }
            
            // Automatizar cálculo de dipolo para Nav1.7
            if (group === "nav1_7") {
                setTimeout(() => calculateDipoleFromDatabase(group, selectedId), 1000);
            } else {
                resetDipoleControls();
            }
        }
    });

    proteinSelect.addEventListener("change", () => {
        const group = groupSelect.value;
        const id = proteinSelect.value;
        loadPDB(group, id);
        
        // Notify dual view manager
        if (window.dualViewManager) {
            const selectedName = proteinSelect.options[proteinSelect.selectedIndex]?.text;
            window.dualViewManager.onDatabaseProteinSelected(group, id, selectedName);
        }
        
        // Automatizar cálculo de dipolo para Nav1.7
        if (group === "nav1_7") {
            setTimeout(() => calculateDipoleFromDatabase(group, id), 1000);
        } else {
            resetDipoleControls();
        }
    });

    // Función para calcular dipolo desde base de datos
    async function calculateDipoleFromDatabase(group, id) {
        if (group !== "nav1_7" || dipoleCalculationInProgress) return;
        
        dipoleCalculationInProgress = true;
        updateDipoleStatus("Calculando dipolo...", "calculating");
        
        try {
            // Usar únicamente el endpoint v2 para el cálculo del dipolo
            const response = await fetch(`/v2/dipole/${group}/${id}`, {
                method: 'POST'
            });
            const payload = await response.json();
            const result = payload.result || payload; // v2 presenter returns {meta, result}
            if (result.success) {
                currentDipoleData = result.dipole;
                updateDipoleStatus("Dipolo calculado - py3Dmol disponible", "ready");
                
                // Mostrar información del dipolo automáticamente
                displayDipoleInfo(currentDipoleData);
                
                // Notificar al dual view manager que el dipolo está listo
                if (window.dualViewManager) {
                    window.dualViewManager.onDipoleCalculated(currentDipoleData);
                }
                
            } else {
                throw new Error(result.error || 'Error desconocido calculando dipolo');
            }
            
        } catch (error) {
            console.error('Error calculating dipole:', error);
            updateDipoleStatus("Error calculando dipolo", "error");
            currentDipoleData = null;
        } finally {
            dipoleCalculationInProgress = false;
        }
    }

    // Función para mostrar información del dipolo - simplificada
    function displayDipoleInfo(dipoleData) {
        // Ya no necesitamos mostrar la información aquí porque se maneja en el panel de análisis
        console.log('Dipole data received:', dipoleData);
    }

    // Función para actualizar el estado del dipolo
    function updateDipoleStatus(text, status) {
        const statusElement = document.getElementById('dipole-status-text');
        const statusContainer = document.getElementById('dipole-status');
        
        if (statusElement) {
            statusElement.textContent = text;
        }
        
        if (statusContainer) {
            statusContainer.className = `dipole-status ${status}`;
        }
    }

    // Función para resetear controles de dipolo - simplificada
    function resetDipoleControls() {
        currentDipoleData = null;
        updateDipoleStatus("Solo disponible para Nav1.7", "disabled");
        
        // Notificar al dual view manager que se resetee el dipolo
        if (window.dualViewManager) {
            window.dualViewManager.resetDipoleState();
        }
    }

    // Event listener para mostrar/ocultar dipolo
    const showDipoleBtn = document.getElementById('show-dipole-btn');
    if (showDipoleBtn) {
        showDipoleBtn.addEventListener('click', async () => {
            if (!currentDipoleData) {
                alert('No hay datos de dipolo disponibles');
                return;
            }
            
            try {
                if (!window.dualViewManager.dipoleVisible) {
                    // Mostrar dipolo
                    await window.dualViewManager.showDipole(currentDipoleData);
                    
                    // Actualizar UI con info de dipolo
                    document.getElementById('dipole-magnitude').textContent = 
                        currentDipoleData.magnitude.toFixed(3);
                    document.getElementById('dipole-direction').textContent = 
                        `[${currentDipoleData.normalized.map(x => x.toFixed(3)).join(', ')}]`;
                    document.getElementById('dipole-info').style.display = 'block';
                    
                    showDipoleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Ocultar Dipolo';
                } else {
                    // Ocultar dipolo
                    await window.dualViewManager.hideDipole();
                    document.getElementById('dipole-info').style.display = 'none';
                    showDipoleBtn.innerHTML = '<i class="fas fa-eye"></i> Mostrar Dipolo';
                }
                
            } catch (error) {
                alert('Error mostrando/ocultando dipolo: ' + error.message);
                console.error('Dipole visualization error:', error);
            }
        });
    }

    // Inicialización
    groupSelect.value = "toxinas";
    loadProteins("toxinas");

    setTimeout(() => {
        if (proteinSelect.options.length > 0) {
            const firstId = proteinSelect.value;
            loadPDB("toxinas", firstId);
        }
    }, 100);

    // File upload handlers (only if elements exist in DOM)
    setupFileUploadHandlers();

    function setupFileUploadHandlers() {
        const pdbFileInput = document.getElementById('pdb-file-input');
        const psfFileInput = document.getElementById('psf-file-input');
        const loadPdbBtn = document.getElementById('load-pdb-btn');
        const loadPsfBtn = document.getElementById('load-psf-btn');
        const toggleDipoleBtn = document.getElementById('toggle-dipole');

        // If the elements are not present in this template, skip attaching handlers
        if (!pdbFileInput || !psfFileInput || !loadPdbBtn || !loadPsfBtn || !toggleDipoleBtn) {
            return;
        }

        let dipoleVisible = false;

        // PDB file upload
        loadPdbBtn.addEventListener('click', () => {
            pdbFileInput.click();
        });

        pdbFileInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (file) {
                try {
                    loadPdbBtn.textContent = '⏳ Cargando...';
                    await window.molstarAnalyzer.loadLocalPDB(file);
                    loadPdbBtn.innerHTML = '<i class="fas fa-check"></i> PDB Cargado';
                    loadPdbBtn.style.background = '#28a745';
                    
                    // Notify dual view manager
                    if (window.dualViewManager) {
                        window.dualViewManager.onLocalStructureLoaded(file.name);
                    }
                    
                } catch (error) {
                    alert('Error cargando PDB: ' + error.message);
                    loadPdbBtn.innerHTML = '<i class="fas fa-upload"></i> Cargar PDB';
                    loadPdbBtn.style.background = '';
                }
            }
        });

        // PSF file upload
        loadPsfBtn.addEventListener('click', () => {
            psfFileInput.click();
        });

        psfFileInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (file) {
                try {
                    await window.molstarAnalyzer.loadLocalPSF(file);
                    loadPsfBtn.innerHTML = '<i class="fas fa-check"></i> PSF Cargado';
                    loadPsfBtn.style.background = '#28a745';
                    
                    // Notify dual view manager
                    if (window.dualViewManager) {
                        window.dualViewManager.onPSFLoaded(file.name);
                    }
                    
                } catch (error) {
                    alert('Error cargando PSF: ' + error.message);
                }
            }
        });

        // Dipole toggle
        toggleDipoleBtn.addEventListener('click', async () => {
            try {
                if (!window.dualViewManager.dipoleVisible) {
                    toggleDipoleBtn.textContent = '⏳ Calculando...';
                    
                    const dipoleData = await window.molstarAnalyzer.calculateAndShowDipole();
                    
                    // Show dipole using dual view manager
                    await window.dualViewManager.showDipole(dipoleData);
                    
                    // Update UI with dipole info
                    document.getElementById('dipole-magnitude').textContent = 
                        dipoleData.magnitude.toFixed(3);
                    document.getElementById('dipole-direction').textContent = 
                        `[${dipoleData.normalized.map(x => x.toFixed(3)).join(', ')}]`;
                    document.getElementById('dipole-info').style.display = 'block';
                    
                } else {
                    await window.dualViewManager.hideDipole();
                    document.getElementById('dipole-info').style.display = 'none';
                }
                
            } catch (error) {
                alert('Error con vector dipolo: ' + error.message);
                toggleDipoleBtn.innerHTML = '<i class="fas fa-arrow-up"></i> Mostrar Dipolo';
                console.error('Dipole error details:', error);
            }
        });
    }
});