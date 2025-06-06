<script lang="ts">
  import { writable } from 'svelte/store';
  import { onMount } from 'svelte';

  export let power = false;
  export let screenCount = '';
  export let matrixCount = '';
  export let screenShape = '';

  export const screenShapes = ["Square", "Line", "Horizontal Rectangle", "Vertical Rectangle"];

  let token: string;

  // Au montage, on récupère l'état courant côté backend
  onMount(async () => {
    token = localStorage.getItem('token') ?? '';

    try {
      // const res = await fetch('http://localhost:8000/api/settings/power', { 
      const res = await fetch('/api/settings/power', { 
        method: 'GET',
        headers: {
                'Authorization': `Bearer ${token}`
            },
      });
      // const res = await fetch('/api/settings/power', { method: 'GET' });
      const json = await res.json();
      power = json.power;
      console.log("L'état de Power : ", json.power);
    } catch (e) {
      console.error("Impossible de charger l'état allumé :", e);
      power = false; // fallback
    }

    try {
      // const resCfg = await fetch('http://localhost:8000/api/settings/config', {
      const resCfg = await fetch('/api/settings/config', {
        method: 'GET',
        headers: {
                'Authorization': `Bearer ${token}`
            },
      });
      // const resCfg = await fetch('/api/settings/config', { method: 'GET' });
      const jsonCfg = await resCfg.json();
      screenCount = jsonCfg.screenCount;
      matrixCount = jsonCfg.matrixCount;
      screenShape = jsonCfg.screenShape;
    } catch (e) {
      console.error("Impossible de charger la configuration :", e);
    }
  });

  async function togglePower() {
    power = !power;
    // await fetch('http://localhost:8000/api/settings/power', {
    await fetch('/api/settings/power', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
       },
      body: JSON.stringify({ power })
    });
  }

  async function submitSettings() {
    const payload = { screenCount, matrixCount, screenShape };
    // await fetch('http://localhost:8000/api/settings/config', {
    await fetch('/api/settings/config', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
       },
      body: JSON.stringify(payload)
    });
    alert("Paramètres écran bien mis à jour !")
  }
</script>

<svelte:head>
  <title>Settings</title>
</svelte:head>

<div class="min-h-screen flex flex-col items-center py-8 px-4">
  <h1 class="text-center text-4xl text-black font-bold mb-8">Screen Settings</h1>

  <div class="w-full max-w-md space-y-6">
    <!-- Power Card -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body items-center">
        <h2 class="card-title">Power</h2>
        <button
          on:click={togglePower}
          class="btn btn-circle btn-outline btn-lg"
          class:btn-success={!power}
          class:btn-error={power}
        >
          {power ? 'Off' : 'On'}
        </button>
      </div>
    </div>

    <!-- Screen Count Card -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body items-center">
        <h2 class="card-title">Number of Screens</h2>
        <input
          type="number"
          min="0"
          max="10"
          bind:value={screenCount}
          class="input input-bordered w-full"
        />
      </div>
    </div>

    <!-- Matrix Count Card -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body items-center">
        <h2 class="card-title">Number of Matrix</h2>
        <input
          type="number"
          min="0"
          max="10"
          bind:value={matrixCount}
          disabled={!screenCount || Number(screenCount) === 0}
          class="input input-bordered w-full disabled:opacity-50"
        />
      </div>
    </div>

    <!-- Screen Shape Card -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body items-center">
        <h2 class="card-title">Screen Shape</h2>
        <select
          bind:value={screenShape}
          disabled={!screenCount || Number(screenCount) === 0}
          class="select select-bordered w-full disabled:opacity-50"
        >
          <option value="" disabled selected>Select shape</option>
          {#each screenShapes as shape}
            <option value={shape}>{shape}</option>
          {/each}
        </select>
      </div>
    </div>

    <!-- Apply Button -->
    <button
      on:click={submitSettings}
      class="btn btn-primary btn-block"
    >
      Apply Settings
    </button>
  </div>
</div>
