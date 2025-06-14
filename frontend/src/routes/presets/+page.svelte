<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import PresetItem from '$lib/components/PresetItem.svelte';
  import DisplayingAds from '$lib/components/Edition/DisplayingAds.svelte';
  import DisplayVisual from '$lib/components/Edition/DisplayVisual.svelte';
  import QRCodeVote from '$lib/components/Edition/QRCodeVote.svelte';
  import RealTimeLyrics from '$lib/components/Edition/RealTimeLyrics.svelte';
  import { isTokenExpired } from '$lib/utils/jwt';

  interface Preset {
    id: number;
    name: string;
    type: string;
    data: any;
  }

  let presets: Preset[] = [];
  let showModal = false;
  let selectedPreset: Preset | null = null;

  let token: string;

  const typeMap = {
    ads: DisplayingAds,
    visual: DisplayVisual,
    qrcode: QRCodeVote,
    lyrics: RealTimeLyrics
  };

  onMount(async () => {
    token = localStorage.getItem('token');
    if (!token || isTokenExpired(token)) {
      alert('Session expirée, veuillez vous reconnecter.');
      localStorage.removeItem('token');
      window.location.href = '/login'; // ou utilise goto('/login') si tu veux éviter un reload complet
    }
  });

  async function loadPresets() {
    try {
      // const res = await fetch('http://localhost:8000/api/presets', {
      const res = await fetch('/api/presets', {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
      });
      // const res = await fetch('/api/presets');
      if (!res.ok) throw new Error('Failed to load presets');
      presets = await res.json();
    } catch (error) {
      console.error(error);
    }
  }


  async function onPlayStop(event: CustomEvent) {
    const preset = presets.find(p => p.id === event.detail.id);
    console.log(preset);

    if (!preset) return;

    // Si preset est indéfini alors on le définit
    const state = preset.data.state ?? "play";
    if (preset.data.state == "play") {
        // await fetch(`http://localhost:8000/api/edition/${preset.type}/play`, {
        await fetch(`/api/edition/${preset.type}/play`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(preset.data)
        });
        preset.data.state = "stop";
        saveModifiedPreset();
    } else if (preset.data.state == "stop") {
        // await fetch(`http://localhost:8000/api/edition/${preset.type}/stop`, {
        await fetch(`/api/edition/${preset.type}/stop`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(preset.data)
        });
        preset.data.state = "play";
        saveModifiedPreset();
    }
  }


  async function onDelete(event: CustomEvent) {
    const preset = presets.find(p => p.id === event.detail.id);
    if (!preset) return;
    if (!confirm(`Supprimer le preset « ${preset.name} » ?`)) return;
    // await fetch(`http://localhost:8000/api/presets/${preset.id}`, { method: 'DELETE' });
    await fetch(`/api/presets/${preset.id}`, { method: 'DELETE' });
    await loadPresets();
  }

  function onModify(event: CustomEvent) {
    const preset = presets.find(p => p.id === event.detail.id);
    if (!preset) return;
    selectedPreset = { ...preset };
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    selectedPreset = null;
  }

  async function saveModifiedPreset() {
    if (!selectedPreset) return;

    const updated = {
      type: selectedPreset.type,
      name: selectedPreset.name,
      data: selectedPreset.data
    };

    console.log('🔧 Tentative de mise à jour du preset :', selectedPreset.id);
    console.log('Payload envoyé :', updated);

    try {
      // const response = await fetch(`http://localhost:8000/api/presets/${selectedPreset.id}`, {
      const response = await fetch(`/api/presets/${selectedPreset.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated)
      });

        console.log('📡 Réponse serveur :', response.status);
        const result = await response.json().catch(() => null);
        if (result) console.log('📨 Contenu réponse :', result);

        if (!response.ok) {
        throw new Error(`Erreur HTTP ${response.status}`);
        }

      closeModal();
      await loadPresets();
    } catch (error) {
      console.error('Erreur lors de la sauvegarde : ', error);
    }
  }

  onMount(loadPresets);
</script>

<svelte:head>
  <title>Saved Presets</title>
</svelte:head>

<div class="min-h-screen bg-pink-50 flex flex-col items-center py-8 px-4">
  <h1 class="text-4xl font-bold mb-8 text-gray-800">Saved Presets</h1>

  <div class="w-full max-w-lg space-y-4">
    {#each presets as preset}
      <PresetItem {preset}
        on:playstop={onPlayStop}
        on:delete={onDelete}
        on:modify={onModify}
      />
    {/each}
  </div>

  {#if showModal && selectedPreset}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-black rounded-xl shadow-lg p-6 w-full max-w-md">
        <h2 class="text-2xl font-semibold mb-4">Modify Preset : {selectedPreset.name}</h2>
        <div class="modal-content bg-gray-800 rounded-lg p-4">
          <svelte:component
            this={typeMap[selectedPreset.type]}
            bind:data={selectedPreset.data}
            editMode={true}
          />
        </div>
        <div class="flex justify-center mt-6">
          <button class="btn btn-primary px-6" on:click={saveModifiedPreset}>Save</button>
        </div>
        <div class="flex justify-center mt-4">
          <button class="btn btn-secondary" on:click={closeModal}>Cancel</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(.modal-content) {
    background-color: #1f2937;
  }
  :global(.modal-content .btn-square),
  :global(.modal-content .btn:not(.btn-primary):not(.btn-secondary)) {
    display: none !important;
  }
</style>