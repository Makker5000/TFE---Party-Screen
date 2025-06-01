<script lang="ts">
  import { onMount } from 'svelte';
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';

  // On stockera ici le fichier choisi
  let file: File | null = null;
  // Boolean qui indique si on est en mode "Play" actif
  let active = false;
  // Nom de fichier généré par FastAPI (UUID + extension), retourné par /upload
  let uploadedFilename: string | null = null;

  // Modal “Save preset”
  let showModal = false;

  function openSavePresetModal() {
    showModal = true;
  }

  async function handleSavePreset(presetName: string) {
    const presetData = {
      type: 'visual',
      name: presetName,
      data: {
        // tu peux ajouter data utiles ici
      }
    };

    try {
      const response = await fetch('/api/presets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
    file = event.target.files[0] ?? null;
  }

  async function toggleVisual() {
    // Si on est en train de lancer et qu’il n’y a pas de fichier, on bloque
    if (!active && !file) {
      return alert("Veuillez choisir un fichier avant de lancer la lecture.");
    }

    if (!active) {
      // === 1) Upload d’abord le fichier vers /upload ===
      const formData = new FormData();
      formData.append('file', file);

      let uploadResponse;
      try {
        // uploadResponse = await fetch('http://localhost:8000/api/edition/visual/upload', {
        uploadResponse = await fetch('/api/edition/visual/upload', {
          method: 'POST',
          body: formData
        });
      } catch (e) {
        console.error('Erreur réseau lors de l\'upload :', e);
        return alert('Échec de l’upload.');
      }

      if (!uploadResponse.ok) {
        console.error('Réponse non-ok de /upload', await uploadResponse.text());
        return alert('Échec de l’upload (status ' + uploadResponse.status + ').');
      }

      const uploadJson = await uploadResponse.json();
      // On récupère le filename (UUID + .png)
      uploadedFilename = uploadJson.filename;
      console.log('Upload réussi, filename =', uploadedFilename);

      // === 2) Dès que l’upload est fait, on envoie le “play” ===
      try {
        // const playResponse = await fetch('http://localhost:8000/api/edition/visual/play', {
        const playResponse = await fetch('/api/edition/visual/play', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ media: uploadedFilename })
        });

        if (!playResponse.ok) {
          console.error('Réponse non-ok de /play', await playResponse.text());
          return alert('Échec du Play (status ' + playResponse.status + ').');
        }

        const playJson = await playResponse.json();
        console.log('Play command envoyé →', playJson);
      } catch (e) {
        console.error('Erreur réseau lors de /play :', e);
        return alert('Échec de la commande Play.');
      }

      // Passe en mode actif
      active = true;
    } else {
      // === 3) On était actif, on envoie donc le “stop” ===
      try {
        // const stopResponse = await fetch('http://localhost:8000/api/edition/visual/stop', {
        const stopResponse = await fetch('/api/edition/visual/stop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        if (!stopResponse.ok) {
          console.error('Réponse non-ok de /stop', await stopResponse.text());
          return alert('Échec du Stop (status ' + stopResponse.status + ').');
        }

        const stopJson = await stopResponse.json();
        console.log('Stop command envoyé →', stopJson);
      } catch (e) {
        console.error('Erreur réseau lors de /stop :', e);
        return alert('Échec de la commande Stop.');
      }

      // On remet tout à zéro
      active = false;
      uploadedFilename = null;
      file = null;
    }
  }
</script>

<div class="flex flex-col items-center space-y-4 py-4">
  <!-- Input de fichier : on ne peut plus changer tant qu’on est en “play” -->
  <input
    type="file"
    accept="image/*,video/*"
    on:change={handleFileChange}
    class="file-input file-input-bordered file-input-accent w-full max-w-xs"
    disabled={active}
  />
  <p class="text-sm">
    Selected file : <span class="font-medium">{file?.name ?? 'None'}</span>
  </p>

  <!-- Boutons Play / Stop et Save (si pas en mode édition) -->
  <div class="flex space-x-2">
    <button
      on:click={toggleVisual}
      class="btn btn-outline btn-lg"
      class:btn-success={!active}
      class:btn-error={active}
    >
      {active ? 'Stop' : 'Play'}
    </button>

    <button
      class="btn btn-outline btn-lg hover:bg-blue-600 border-blue-200 hover:border-blue-600"
      on:click={openSavePresetModal}
      disabled={active}
    >
      Save
    </button>
  </div>

  <SavePresetModal
    open={showModal}
    on:save={(e) => handleSavePreset(e.detail)}
    on:cancel={() => (showModal = false)}
  />
</div>
