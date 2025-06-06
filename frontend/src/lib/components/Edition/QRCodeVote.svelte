<script lang="ts">
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';
    import { onMount } from 'svelte';

  let url = '';
  let defaultUrl = 'http://localhost:5173/lyrics';

  let currentUrl = url || defaultUrl;
  
  // NOUVEAU: Variables pour l'affichage de l'image
  let qrImageSrc = '';
  let qrGenerated = false;
  let isLoading = false;

  // Var pour stocker le filename renvoyé par le backend
  let qrFilename: string | null = null;
  let qrId: number | null = null;

  export let editMode: boolean = false;
  let active = false;
  let showModal = false;

  let state = active ? 'stop' : 'play';

  export let data: {
    url: string;
    state: string;
  } = {
    url: currentUrl,
    state: state
  }; 

  let token: string;

  onMount(async () => {
    token = localStorage.getItem('token') ?? '';
  });

  function openSavePresetModal() {
    showModal = true;
  }

  async function handleSavePreset(presetName: string) {
    const presetData = {
      type: 'qrcode',
      name: presetName,
      data: {
        ...data
      }
    };

    console.log('Saving preset:', presetData);
    
    try {
        // const response = await fetch('http://localhost:8000/api/presets', {
        const response = await fetch('/api/presets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
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
    qrGenerated = false;
    qrFilename = null;
    
    try {
      // const response = await fetch('http://localhost:8000/api/edition/qrcode', {
      const response = await fetch('/api/edition/qrcode', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url: currentUrl })
      });
      
      if (!response.ok) {
        let detail = `Status ${response.status}`;
        try {
          const err = await response.json();
          if (err.detail) detail = err.detail;
        } catch {}
        // throw new Error('Erreur lors de la génération du QR Code');
        throw new Error(detail);
      }
      
      // NOUVEAU: Récupérer l'image du QR Code et le filename
      const result = await response.json();
      qrImageSrc = result.image;
      qrGenerated = true;
      qrFilename = result.filename;
      
      console.log('QR Code généré:', result);
      
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la génération du QR Code');
    } finally {
      isLoading = false;
    }
  }

  async function toggleQr() {

    if (!qrGenerated || qrId === null) {
      state = active ? 'play' : 'stop';
      // Si le preset envoie juste data.url, on peut faire l'appel directement à /play avec { url }
      // afin de créer le record DB à la volée. Par défaut, on prend qrId si déjà généré localement.
      data = { url: data.url, state };
      if (data) {
        try {
          // const response = await fetch('http://localhost:8000/api/edition/qrcode/play', {
          const response = await fetch('/api/edition/qrcode/play', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
          });
          if (!response.ok) {
            let detail = `Status ${response.status}`;
            try { const err = await response.json(); if (err.detail) detail = err.detail; } catch {}
            throw new Error(detail);
          }
          const resPlay = await response.json();
          qrId = resPlay.id; // si le backend a généré le record à la volée
          active = true;
        } catch (err) {
          console.error('Erreur Play QR:', err);
          alert('Erreur lors du play du QR Code : ' + err);
        }
        return;
      } else {
        alert('Impossible de jouer : ni QR généré ni URL fournie.');
        return;
      }
    }

    // Si qrId existe, on appelle /stop ou /play selon active
    const endpoint = active
      ? '/api/edition/qrcode/stop'
      : '/api/edition/qrcode/play';
    // const endpoint = active
    //   ? 'http://localhost:8000/api/edition/qrcode/stop'
    //   : 'http://localhost:8000/api/edition/qrcode/play';
    const payload = { id: qrId, state };

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        let detail = `Status ${response.status}`;
        try { const err = await response.json(); if (err.detail) detail = err.detail; } catch {}
        throw new Error(detail);
      }
      active = !active;
    } catch (err) {
      console.error('Erreur toggle QR :', err);
      alert('Erreur lors du ' + (active ? 'stop' : 'play') + ' du QR : ' + err);
    }
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