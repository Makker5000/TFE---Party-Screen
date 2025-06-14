<script lang="ts">
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';
  import { onMount } from 'svelte';

  let textColor = 'white';
  let backgroundColor = 'black';
  let font = 'Arial';
  let animation = 'scroll_left';
  let speed = 1;
  let content = '';
  // let state = 'stop';
  let availableTextColors = ['white', 'red', 'green', 'blue', 'yellow', 'purple'];
  let availableBgColors = ['white', 'red', 'green', 'blue', 'yellow', 'purple', 'black'];
  let availableFonts = ['Arial', 'Verdana'];
  let availableAnimations = ['scroll_left', 'scroll_right', 'bounce', 'none'];

  let active = false;

  export let data: {
    textColor: string;
    backgroundColor: string;
    font: string;
    animation: string;
    speed: number;
    content: string;
    state: 'play' | 'stop'; 
  } = {
    textColor: textColor,
    backgroundColor: backgroundColor,
    font: font,
    animation: animation,
    speed: speed,
    content: content,
    state: 'play',
  };
  export let editMode: boolean = false;
  let showModal = false;

  let token: string;

  onMount(async () => {
    token = localStorage.getItem('token') ?? '';
    // active = data.state === 'stop';
  });


  function openSavePresetModal() {
    showModal = true;
  }

  async function handleSavePreset(presetName: string) {
    const presetData = { 
      type: 'ads',
      name: presetName,
      data: { ...data } };
    // const url = 'http://localhost:8000/api/presets';
    const url = '/api/presets';
    await fetch(url, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(presetData)
    });
    showModal = false;
  }

  async function toggleAds() {
    // const config = { ...data, state: active ? 'stop' : 'play' };
    const nextState = active ? 'play' : 'stop';
    data = { ...data, state: nextState };

    // const url = active ? 'http://localhost:8000/api/edition/ads/stop' : 'http://localhost:8000/api/edition/ads/play';
    const url = active ? '/api/edition/ads/stop' : '/api/edition/ads/play';
    await fetch(url, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    active = !active;
  }
</script>

<div class="flex flex-col items-center space-y-4 py-4 text-white">
  <div class="w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Text Color</span></label>
    <select bind:value={data.textColor} class="select select-bordered w-full">
      {#each availableTextColors as color}
        <option value={color}>{color}</option>
      {/each}
    </select>
  </div>

  <div class="w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Background Color</span></label>
    <select bind:value={data.backgroundColor} class="select select-bordered w-full">
      {#each availableBgColors as color}
        <option value={color}>{color}</option>
      {/each}
    </select>
  </div>

  <div class="w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Font</span></label>
    <select bind:value={data.font} class="select select-bordered w-full" disabled>
      {#each availableFonts as f}
        <option value={f}>{f}</option>
      {/each}
    </select>
  </div>

  <div class="w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Animation</span></label>
    <select bind:value={data.animation} class="select select-bordered w-full">
      {#each availableAnimations as a}
        <option disabled={a == 'bounce'} value={a}>{a}</option>
      {/each}
    </select>
  </div>

  <div class="w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Speed</span></label>
    <input type="range" min="0" max="10" step="1" bind:value={data.speed} class="range range-accent w-full" />
  </div>

  <div class="w-full max-w-xs">
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label class="label"><span class="label-text">Content</span></label>
    <input type="text" bind:value={data.content} placeholder="Enter a message" class="input input-bordered w-full" />
  </div>

  {#if !editMode}
    <div class="flex space-x-2">
      <button
        on:click={toggleAds}
        class="btn btn-outline btn-lg"
        class:btn-success={!active}
        class:btn-error={active}
      >
        {active ? 'Stop' : 'Play'}
      </button>
      <button 
        class="btn btn-outline btn-lg hover:bg-blue-600 border-blue-200 hover:border-blue-600"
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