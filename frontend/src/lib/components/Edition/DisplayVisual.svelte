<script lang="ts">
  import { onMount } from 'svelte';
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';
  import { Input } from 'postcss';

  const formData = new FormData;

  export let data: {
    formData: FormData;
  } = {
    formData: formData,
  };

  export let editMode: boolean = false;
  let file = null;
  let active = false;

  let showModal = false;

  function openSavePresetModal() {
    showModal = true;
  }

  async function handleSavePreset(presetName: string) {
    // Ce sera l'objet qu'on enverra au backend plus tard
    const presetData = {
      type: 'visual',
      name: presetName,
      data: {
        ...data,
      }
    };

    console.log('Saving preset:', presetData);
    
    try {
    //   const response = await fetch('http://localhost:8000/api/presets', {
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

      console.log('Preset Visual enregistré avec succès');
    } catch (error) {
      console.error('Erreur:', error);
    }

    showModal = false;
  }

  function handleFileChange(event) {
    file = event.target.files[0];
  }

  async function toggleVisual() {
    if (!active && !file) {
      return alert("Veuillez choisir un fichier avant de lancer la lecture.");
    }

    const url = active
      // ? 'http://localhost:8000/api/edition/visual/upload'
      ? '/api/edition/visual/stop'
      // ? 'http://localhost:8000/api/edition/visual/stop'
      : '/api/edition/visual/upload';
    const options = active
      ? {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ media: 'none' })
        }
      : (() => {
          const formData = new FormData();
          formData.append('file', file);
          return { method: 'POST', body: formData };
        })();

    const res = await fetch(url, options);
    console.log(await res.json());

    active = !active;
  }
</script>

<div class="flex flex-col items-center space-y-4 py-4">
  <!-- Input de fichier -->
  <input
    type="file"
    accept="image/*,video/*"
    on:change={handleFileChange}
    class="file-input file-input-bordered file-input-accent w-full max-w-xs"
    disabled={active}
  />
  <p class="text-sm">
    Selected file&nbsp;: <span class="font-medium">{file?.name ?? 'None'}</span>
  </p>

  {#if !editMode}
    <div class="flex space-x-2">
      <button
        on:click={toggleVisual}
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

<SavePresetModal
  open={showModal}
  on:save={(e) => handleSavePreset(e.detail)}
  on:cancel={() => (showModal = false)}
/>