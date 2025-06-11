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

            // Obtener los datos PDB del servidor
            const res = await fetch(`/get_pdb/${group}/${id}`);
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
    // Cuando cambiemos el grupo de proteínas, cargamos las proteínas correspondientes
    groupSelect.addEventListener("change", () => {
        const group = groupSelect.value;
        loadProteins(group);
        
        
        const selectedId = proteinSelect.value;
        if (selectedId) loadPDB(group, selectedId);
    });

    proteinSelect.addEventListener("change", () => {
        const group = groupSelect.value;
        const id = proteinSelect.value;
        loadPDB(group, id);
    });


    groupSelect.value = "toxinas";
  
    loadProteins("toxinas");

    setTimeout(() => {
        if (proteinSelect.options.length > 0) {
            const firstId = proteinSelect.value;
            loadPDB("toxinas", firstId);
        }
    }, 100);

    // File upload handlers
    setupFileUploadHandlers();

    function setupFileUploadHandlers() {
        const pdbFileInput = document.getElementById('pdb-file-input');
        const psfFileInput = document.getElementById('psf-file-input');
        const loadPdbBtn = document.getElementById('load-pdb-btn');
        const loadPsfBtn = document.getElementById('load-psf-btn');
        const toggleDipoleBtn = document.getElementById('toggle-dipole');

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
                    
                    // Enable PSF loading
                    loadPsfBtn.disabled = false;
                    
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
                    
                    // Enable dipole calculation
                    toggleDipoleBtn.disabled = false;
                    
                } catch (error) {
                    alert('Error cargando PSF: ' + error.message);
                }
            }
        });

        // Dipole toggle
        toggleDipoleBtn.addEventListener('click', async () => {
            try {
                if (!dipoleVisible) {
                    toggleDipoleBtn.textContent = '⏳ Calculando...';
                    
                    const dipoleData = await window.molstarAnalyzer.calculateAndShowDipole();
                    
                    // Try py3Dmol first (best for molecular visualization)
                    try {
                        await window.molstarAnalyzer.showDipoleInPy3Dmol(dipoleData);
                        console.log("Using py3Dmol visualization for dipole");
                    } catch (py3dmolError) {
                        console.log("py3Dmol failed, trying Plotly visualization");
                        try {
                            await window.molstarAnalyzer.showDipoleInPlotly(dipoleData);
                        } catch (plotlyError) {
                            console.log("Both py3Dmol and Plotly failed, trying Mol* visualization");
                            try {
                                await window.molstarAnalyzer.visualizeDipoleVector(dipoleData);
                            } catch (molstarError) {
                                console.log("All visualizations failed, showing info only");
                                window.molstarAnalyzer.showDipoleInfo(dipoleData);
                            }
                        }
                    }
                    
                    // Update UI with dipole info
                    document.getElementById('dipole-magnitude').textContent = 
                        dipoleData.magnitude.toFixed(3);
                    document.getElementById('dipole-direction').textContent = 
                        `[${dipoleData.normalized.map(x => x.toFixed(3)).join(', ')}]`;
                    document.getElementById('dipole-info').style.display = 'block';
                    
                    toggleDipoleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Ocultar Dipolo';
                    dipoleVisible = true;
                    
                } else {
                    await window.molstarAnalyzer.removeDipoleVector();
                    document.getElementById('dipole-info').style.display = 'none';
                    toggleDipoleBtn.innerHTML = '<i class="fas fa-arrow-up"></i> Mostrar Dipolo';
                    dipoleVisible = false;
                }
                
            } catch (error) {
                alert('Error con vector dipolo: ' + error.message);
                toggleDipoleBtn.innerHTML = '<i class="fas fa-arrow-up"></i> Mostrar Dipolo';
                console.error('Dipole error details:', error);
            }
        });
    }
});