<script>
    export let file = null;

    function handleFileChange(event) {
        file = event.target.files[0];
    }

    async function playVisual() {
        // const payload = {
		// 	file: $file,
		// };

        if (!file) {
            alert("Veuillez choisir un fichier.");
            return;
        }

        const formData = new FormData();
        // formData.append('file', payload);
        formData.append('file', file);

        const res = await fetch('http://localhost:8000/api/edition/visual/upload', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        console.log(data);
    }

    async function stopVisual(){
        await fetch('http://localhost:8000/api/edition/visual/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ media: "none" })
        });
    }
</script>
  
<div class="section">
    <h2>Display of Artist Visuals</h2>
    <!-- <input type="file" accept="image/*,video/*" on:change={(e) => onUpload(e)} /> -->
    <!-- <input type="file" accept="image/*,video/*" bind:value={file} /> -->
    <input type="file" accept="image/*,video/*" on:change={handleFileChange} />
    <p>Fichier sélectionné : {file ? file.name : 'Aucun'}</p>

    <button on:click={() => playVisual()} > Play </button>
    <button on:click={() => stopVisual()} >Stop</button>
    <button disabled >Save</button>
</div>