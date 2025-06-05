<script lang="ts">
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';

  let url = '';
  let defaultUrl = 'http://localhost:5173/lyrics';

  let currentUrl = url || defaultUrl;
  
  // NOUVEAU: Variables pour l'affichage de l'image
  let qrImageSrc = '';
  let qrGenerated = false;
  let isLoading = false;

  export let data: {
    url: string;
  } = {
    url: currentUrl,
  };

  export let editMode: boolean = false;
  let active = false;
  let showModal = false;

  function openSavePresetModal() {
    showModal = true;
  }

  async function handleSavePreset(presetName: string) {
    const presetData = {
      type: 'qrcode',
      name: presetName,
      data: {
        url: currentUrl,
      }
    };

    console.log('Saving preset:', presetData);
    
    try {
        // const response = await fetch('http://localhost:8000/api/presets', {
        const response = await fetch('/api/presets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(presetData)
        });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'enregistrement du preset');
      }

      console.log('Preset QRCode enregistré avec succès');
    } catch (error) {
      console.error('Erreur:', error);
    }

    showModal = false;
  }

  async function generateQRCode() {
    currentUrl = data.url;
    if (!currentUrl) {
      alert('Veuillez saisir une URL.');
      return;
    }
    
    isLoading = true;
    
    try {
      // const response = await fetch('http://localhost:8000/api/edition/qrcode', {
      const response = await fetch('/api/edition/qrcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: currentUrl })
      });
      
      if (!response.ok) {
        throw new Error('Erreur lors de la génération du QR Code');
      }
      
      // NOUVEAU: Récupérer l'image du QR Code
      const result = await response.json();
      qrImageSrc = result.image;
      qrGenerated = true;
      
      console.log('QR Code généré:', result);
      
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la génération du QR Code');
    } finally {
      isLoading = false;
    }
  }

  async function toggleQr() {
    if (!active && !currentUrl) {
      alert('Veuillez générer un QR Code avant de lancer la lecture.');
      return;
    }
    const endpoint = active
      ? '/api/edition/qrcode/stop'
      : '/api/edition/qrcode/play';
    // const endpoint = active
    //   ? 'http://localhost:8000/api/edition/qrcode/stop'
    //   : 'http://localhost:8000/api/edition/qrcode/play';
    const payload = { url: active ? 'stop' : 'play' };

    await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    active = !active;
  }
</script>

<div class="flex flex-col items-center space-y-4 py-4">
  <!-- Input URL -->
  <input
    type="text"
    bind:value={data.url}
    placeholder="Enter URL..."
    class="input input-bordered w-full max-w-xs"
  />

  {#if !editMode}
    <!-- Bouton Générer -->
    <button 
      on:click={generateQRCode} 
      class="btn btn-primary btn-sm w-full max-w-xs"
      disabled={isLoading}
    >
      {#if isLoading}
        <span class="loading loading-spinner loading-sm"></span>
        Génération...
      {:else}
        Générer QR Code
      {/if}
    </button>

    <!-- NOUVEAU: Affichage du QR Code -->
    {#if qrGenerated && qrImageSrc}
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body items-center text-center p-4">
          <h3 class="card-title text-sm">QR Code généré</h3>
          <img 
            src={qrImageSrc} 
            alt="QR Code" 
            class="border-2 border-gray-300 rounded"
            style="image-rendering: pixelated; image-rendering: -moz-crisp-edges; image-rendering: crisp-edges;"
          />
          <p class="text-xs text-gray-500 break-all">{currentUrl}</p>
        </div>
      </div>
    {/if}
    
    <div class="flex space-x-2">
      <button
        on:click={toggleQr}
        class="btn btn-outline btn-sm btn-lg"
        class:btn-success={!active}
        class:btn-error={active}
        disabled={!qrGenerated}
      >
        {active ? 'Stop' : 'Play'}
      </button>
      <button 
        class="btn btn-outline btn-sm btn-lg hover:bg-blue-600 border-blue-200 hover:border-blue-600"
        on:click={openSavePresetModal}
      >
        Save
      </button>
    </div>
    <SavePresetModal
      open={showModal}
      on:save={(e) => handleSavePreset(e.detail)}
      on:cancel={() => (showModal = false)}
    />
  {/if}
</div>