<script lang="ts">
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';
    import { onMount } from 'svelte';
    import AlertModal from '../modals/AlertModal.svelte';
    import Toast from '../modals/Toast.svelte';

  let url = '';
  let defaultUrl = 'https://tfe-twampi.vercel.app/';

  let currentUrl = url || defaultUrl;

  let showOnMatrices = true; 
  
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

  let state = active ? 'play' : 'stop';

  export let data: {
    url: string;
    state: string;
  } = {
    url: currentUrl,
    state: 'play'
  }; 

  // Variables pour récup la config de l'écran actuel
  let screenCount: number = 1;
  let matrixCount: number = 4;
  let screenShape: string = "Square";

  // Liste des 4 combinaisons autorisées
  const validCombos: [number, number, string][] = [
    [1, 9, "Square"],
  ];

  let token: string;

  let showAlertModal = false;
  let alertTitle: string;
  let alertMessage: string;

  let showToast = false;
  let toastMessage = '';
  let toastType = '';

  function triggerToast(msg: string, type = 'info') {
    toastMessage = msg;
    toastType = type;
    showToast = true;
  }

  function closeToast() {
    showToast = false;
  }

  function triggerAlert() {
    showAlertModal = true;
  }

  function closeModal() {
    showAlertModal = false;
  }

  onMount(async () => {
    token = localStorage.getItem('token') ?? '';
    // active = data.state === 'play';

    try {
      // const res = await fetch('http://localhost:8000/api/settings/config', { 
      const res = await fetch('/api/settings/config', { 
        method: 'GET',
        headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` // à adapter selon ta gestion
            }
       });
      // const res = await fetch('/api/settings/config', { method: 'GET' });
      if (!res.ok) {
        console.error('Impossible de charger les settings (status ' + res.status + ')');
        return;
      }
      const json = await res.json();
      screenCount = json.screenCount;
      matrixCount = json.matrixCount;
      screenShape = json.screenShape;
      console.log("Settings récupérés :", screenCount, matrixCount, screenShape);
    } catch (e) {
      console.error("Erreur réseau lors de la récupération des settings :", e);
    }
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

  function isCurrentConfigValid(): boolean {
    return validCombos.some(
      ([sc, mc, shape]) =>
        sc === screenCount && mc === matrixCount && shape === screenShape
    );
  }

  async function generateQRCode() {
    currentUrl = data.url;
    if (!currentUrl) {
      // alert('Veuillez saisir une URL.');
      alertTitle = "Warning";
      alertMessage = "Please enter a URL ! ";
      triggerAlert();
      return;
    }

    if (!isCurrentConfigValid()) {
      alertTitle = "Invalid config !";
      alertMessage = "Your screen settings (" +
          `screenCount=${screenCount}, matrixCount=${matrixCount}, screenShape='${screenShape}'` +
          `) are not part of the authorized combinations :\n` +
          "• (1, 9, 'Square')\n";
      triggerAlert();
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
      
      // Récupérer l'image du QR Code et le filename
      const result = await response.json();
      qrImageSrc = result.image;
      qrGenerated = true;
      qrFilename = result.filename;
      qrId = result.id;
      
      console.log('QR Code généré:', result);
      
    } catch (error) {
      console.error('Erreur:', error);
      // alert('Erreur lors de la génération du QR Code');
      toastMessage = "Error while generating QR Code...";
      toastType = 'error';
      triggerToast(toastMessage, toastType);
    } finally {
      isLoading = false;
    }
  }

  async function toggleQr() {

    if ((!qrGenerated || qrId === null) && state == "play" ) {
        // alert('Impossible de jouer : ni QR généré ni URL fournie.');
        toastMessage = "Unable to play : No QR generated or URL provided.";
        toastType = 'error';
        triggerToast(toastMessage, toastType);
        return;
    }

    // Si qrId existe, on appelle /stop ou /play selon active
    // const endpoint = active
    //   ? '/api/edition/qrcode/stop'
    //   : '/api/edition/qrcode/play';
    // const endpoint = active
    //   ? 'http://localhost:8000/api/edition/qrcode/stop'
    //   : 'http://localhost:8000/api/edition/qrcode/play';

    const base = active
      ? '/api/edition/qrcode/stop'
      : '/api/edition/qrcode/play';
    // const base = active
    //   ? 'http://localhost:8000/api/edition/qrcode/stop'
    //   : 'http://localhost:8000/api/edition/qrcode/play';
    const action = showOnMatrices ? 'display' : 'hide';
    
    const endpoint = `${base}/${action}`;
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
      qrId = null;
    } catch (err) {
      console.error('Erreur toggle QR :', err);
      // alert('Erreur lors du ' + (active ? 'stop' : 'play') + ' du QR : ' + err);
      toastMessage = "Error during state '" + (active ? 'stop' : 'play') + "' of QR : " + err;
      toastType = 'error';
      triggerToast(toastMessage, toastType);
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

    <!-- Affichage du QR Code -->
    {#if qrGenerated && qrImageSrc}
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body items-center text-center p-4">
          <h3 class="card-title text-sm">QR Code généré</h3>
          <img 
            src={qrImageSrc} 
            alt="QR Code" 
            class="border-2 border-gray-300 rounded w-full h-auto max-w-[128px]"
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
        disabled={!qrGenerated}
        on:click={openSavePresetModal}
      >
        Save
      </button>
    </div>
    <div>
      <button 
      on:click={() => showOnMatrices = !showOnMatrices} 
      class="btn btn-outline btn-sm hover:bg-pink-400 border-grey-200 hover:border-pink-600">
        {showOnMatrices ? 'Display QR : YES' : 'Display QR : NO'}
      </button>
    </div>
    <SavePresetModal
      open={showModal}
      on:save={(e) => handleSavePreset(e.detail)}
      on:cancel={() => (showModal = false)}
    />
  {/if}

  <AlertModal
    show={showAlertModal}
    title={alertTitle}
    message={alertMessage}
    onClose={closeModal}
  />

  <Toast
    show={showToast}
    message={toastMessage}
    type={toastType}
    onClose={closeToast}
  />
</div>