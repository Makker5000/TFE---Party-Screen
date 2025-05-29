<script lang="ts">
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';

  let url = '';
  let defaultUrl = 'http://localhost:5173/lyrics';


  let currentUrl = url || defaultUrl;

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
    // Ce sera l'objet qu'on enverra au backend plus tard
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
        throw new Error('Erreur lors de l’enregistrement du preset');
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
    // await fetch('http://localhost:8000/api/edition/qrcode', {
    await fetch('/api/edition/qrcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: currentUrl })
    });
  }

  async function toggleQr() {
    if (!active && !currentUrl) {
      alert('Veuillez générer un QR Code avant de lancer la lecture.');
      return;
    }
    const endpoint = active
      // ? 'http://localhost:8000/api/edition/stop'
      ? '/api/edition/qrcode/stop'
      // ? 'http://localhost:8000/api/edition/play'
      : '/api/edition/qrcode/play';
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
    <button on:click={generateQRCode} class="btn btn-primary btn-sm w-full max-w-xs">
        Générer QR Code
    </button>

    
    <div class="flex space-x-2">
      <button
        on:click={toggleQr}
        class="btn btn-outline btn-sm btn-lg"
        class:btn-success={!active}
        class:btn-error={active}
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