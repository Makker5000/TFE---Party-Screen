<script lang="ts">
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';
  import { onMount } from 'svelte';


  let textColor = 'white';
  let backgroundColor = 'none';
  let font = 'Arial';
  let animation = 'none';
  let availableTextColors = ['white', 'red', 'green', 'blue', 'yellow', 'purple'];
  let availableBgColors = ['white', 'red', 'green', 'blue', 'yellow', 'purple', 'none'];
  let availableFonts = ['Arial', 'Times New Roman', 'Comic Sans MS'];
  let availableAnimations = ['scroll_left', 'scroll_right', 'bounce', 'none'];

  export let data: {
    textColor: string;
    backgroundColor: string;
    font: string;
    animation: string;   
  } = {
    textColor: textColor,
    backgroundColor: backgroundColor,
    font: font,
    animation: animation,
  };

  export let editMode: boolean = false;
  let active = false;
  let showModal = false;

  let token: string;

  onMount(async () => {
    token = localStorage.getItem('token') ?? '';
  });

  function openSavePresetModal() {
    showModal = true;
  }

  async function handleSavePreset(presetName: string) {
    // Ce sera l'objet qu'on enverra au backend plus tard
    const presetData = {
      type: 'lyrics',
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
        throw new Error('Erreur lors de l’enregistrement du preset');
      }

      console.log('Preset Lyrics enregistré avec succès');
    } catch (error) {
      console.error('Erreur:', error);
    }

    showModal = false;
  }

  async function toggleLyrics() {
    if (!active) {
      // const config = { textColor, backgroundColor, font, animation };
      const config = { ...data, state: active ? 'stop' : 'play' };
      // const config = { ...data };
      // await fetch('http://localhost:8000/api/edition/lyrics/play', {
      await fetch('/api/edition/lyrics/play', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });
      console.log('Play Real-time Lyrics:', config);
    } else {
      // await fetch('http://localhost:8000/api/edition/lyrics/stop', { method: 'POST' });
      await fetch('/api/edition/lyrics/stop', { method: 'POST' });
      console.log('Stop Real-time Lyrics');
    }
    active = !active;
  }
</script>

<div class="flex flex-col items-center space-y-4 py-4">
  <!-- Text Color -->
  <div class="flex flex-col items-start w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Text Color</span></label>
    <select bind:value={data.textColor} class="select select-bordered w-full">
      {#each availableTextColors as color}
        <option value={color}>{color}</option>
      {/each}
    </select>
  </div>

  <!-- Background Color -->
  <div class="flex flex-col items-start w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Background Color</span></label>
    <select bind:value={data.backgroundColor} class="select select-bordered w-full">
      {#each availableBgColors as color}
        <option value={color}>{color}</option>
      {/each}
    </select>
  </div>

  <!-- Font -->
  <div class="flex flex-col items-start w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Font</span></label>
    <select bind:value={data.font} class="select select-bordered w-full">
      {#each availableFonts as f}
        <option value={f}>{f}</option>
      {/each}
    </select>
  </div>

  <!-- Animation -->
  <div class="flex flex-col items-start w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Animation</span></label>
    <select bind:value={data.animation} class="select select-bordered w-full">
      {#each availableAnimations as a}
        <option value={a}>{a}</option>
      {/each}
    </select>
  </div>

  <!-- Boutons Toggle et Save -->
  {#if !editMode}
    <div class="flex space-x-2">
      <button
        on:click={toggleLyrics}
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