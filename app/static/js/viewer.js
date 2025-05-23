document.addEventListener("DOMContentLoaded", async () => {
    const proteinData = JSON.parse(document.getElementById("protein-data").textContent);
    const toxinasData = proteinData.toxinas;
    const navsData = proteinData.nav1_7;

    const viewerElement = document.getElementById("viewer");

    // Inicialización con opciones explícitas para controlar el tamaño
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
    }

    async function loadPDB(group, id) {
        console.log(`📦 Solicitando estructura de ${group} con ID ${id}`);
        try {
            // Intento más agresivo de limpiar el visor
            try {
                
                await plugin.plugin?.clear?.();
                await plugin.resetCamera?.();
                await plugin.resetStructure?.();
                
            } catch (clearError) {
                console.warn("No se pudo limpiar el visor:", clearError);
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

            // Crear un blob y URL para el archivo PDB
            const blob = new Blob([pdbText], { type: 'chemical/x-pdb' });
            const blobUrl = URL.createObjectURL(blob);
            
            try {
                // Cargar la estructura usando el método correcto con parámetros ajustados
                await plugin.loadStructureFromUrl(blobUrl, 'pdb');  // Usa 'pdb' como segundo parámetro directo, no como objeto
                
                // Aplicar la representación después de cargar
                //await plugin.applyPreset('cartoon');  // Usa un preset estándar
                
                console.log("✅ Estructura cargada correctamente");
            } finally {
                // Liberar el URL del blob
                URL.revokeObjectURL(blobUrl);
            }
        } catch (error) {
            console.error("❌ Error cargando PDB:", error);
            alert("Error al cargar la estructura: " + error.message);
        }
    }

    groupSelect.addEventListener("change", () => {
        const group = groupSelect.value;
        loadProteins(group);
        setTimeout(() => {
            const selectedId = proteinSelect.value;
            if (selectedId) loadPDB(group, selectedId);
        }, 300);
    });

    proteinSelect.addEventListener("change", () => {
        const group = groupSelect.value;
        const id = proteinSelect.value;
        loadPDB(group, id);
    });

    // Inicial: toxinas
    loadProteins("toxinas");
    setTimeout(() => {
        const selectedId = proteinSelect.value;
        if (selectedId) loadPDB("toxinas", selectedId);
    }, 300);
});