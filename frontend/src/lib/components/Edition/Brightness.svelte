<script>
  import { onMount } from 'svelte';

  // On ignore la prop exportée si tu ne l'utilises plus
  // export let brightness = 55;
  let currentBrightness = 0; 

  // Au montage, on récupère l'état courant côté backend
  onMount(async () => {
    try {
      // const res = await fetch('http://localhost:8000/api/edition/brightness');
      const res = await fetch('/api/edition/brightness');
      const json = await res.json();
      currentBrightness = json.brightness ?? 0;
    } catch (e) {
      console.error('Impossible de charger la luminosité :', e);
      currentBrightness = 55; // fallback
    }
  });

  // Envoi uniquement quand l'utilisateur lâche le slider
  async function handleChange() {
    try {
      // await fetch('http://localhost:8000/api/edition/brightness', {
      await fetch('/api/edition/brightness', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brightness: currentBrightness })
      });
    } catch (e) {
      console.error('Échec de l\'update brightness :', e);
    }
  }
</script>

<div class="flex justify-center items-center py-4">
  <input
    type="range"
    min="10"
    max="170"
    bind:value={currentBrightness}
    on:change={handleChange}
    class="range range-accent range-lg w-3/4"
  />
</div>
