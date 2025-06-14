<script lang="ts">
  import { onMount } from 'svelte';
  import SavePresetModal from '$lib/components/modals/SavePresetModal.svelte';
    import AlertModal from '../modals/AlertModal.svelte';
    import Toast from '../modals/Toast.svelte';

  let token: string;

  // On stockera ici le fichier choisi
  let file: File | null = null;
  // Boolean qui indique si on est en mode "Play" actif
  let active = false;
  // Nom de fichier généré par FastAPI (UUID + extension), retourné par /upload
  let uploadedFilename: string | null = null;

  // Modal “Save preset”
  let showModal = false;

  // Variables pour récup la config de l'écran actuel
  let screenCount: number = 1;
  let matrixCount: number = 4;
  let screenShape: string = "Square";

  // Liste des 4 combinaisons autorisées
  const validCombos: [number, number, string][] = [
    [1, 4, "Square"],
    [1, 9, "Square"],
    [1, 6, "Horizontal Rectangle"],
    [1, 6, "Vertical Rectangle"]
  ];

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

  // On va récup au montage la config de l'écran
  onMount(async () => {
    token = localStorage.getItem('token') ?? '';

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
    if (!uploadedFilename) {
      // return alert("Vous devez d’abord uploader une image avant de sauvegarder le preset.");
      alertTitle = "Warning";
      alertMessage = "You have to upload a picture before saving preset ! ";
      triggerAlert();
      return;
    }

    const presetData = {
      type: 'visual',
      name: presetName,
      data: {
        media: uploadedFilename,
        state: 'play'
      }
    };

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
      console.log('Preset Visual enregistré avec succès');
    } catch (error) {
      console.error('Erreur:', error);
    }

    showModal = false;
  }

  function handleFileChange(event) {
    file = event.target.files[0] ?? null;
    console.log("Fichier sélectionné :", file);
  }

  // On vérifie si la Config est correcte 
  function isCurrentConfigValid(): boolean {
    return validCombos.some(
      ([sc, mc, shape]) =>
        sc === screenCount && mc === matrixCount && shape === screenShape
    );
  }

  async function toggleVisual() {
    // Si on est en train de lancer et qu’il n’y a pas de fichier, on bloque
    if (!active && !file) {
      // return alert("Veuillez choisir un fichier avant de lancer la lecture.");
      alertTitle = "Warning";
      alertMessage = "You have to upload a picture before playing preset ! ";
      triggerAlert();
      return;
    }

    if (!active) {
      // On vérifie la config et si elle est bonne alors on upload et traite l'image
      if (!isCurrentConfigValid()) {
        alertTitle = "Invalid config !";
        alertMessage = "Your screen settings (" +
            `screenCount=${screenCount}, matrixCount=${matrixCount}, screenShape='${screenShape}'` +
            `) are not part of the authorized combinations :\n` +
            "• (1, 4, 'Square')\n" +
            "• (1, 9, 'Square')\n" +
            "• (1, 6, 'Horizontal Rectangle')\n" +
            "• (1, 6, 'Vertical Rectangle')";
        triggerAlert();
        return;
      }

      // === 1) Upload d’abord le fichier vers /upload ===
      const formData = new FormData();
      formData.append('file', file);

      let uploadResponse;
      try {
        // uploadResponse = await fetch('http://localhost:8000/api/edition/visual/upload', {
        uploadResponse = await fetch('/api/edition/visual/upload', {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
      } catch (e) {
        console.error('Erreur réseau lors de l\'upload :', e);
        // return alert('Échec de l’upload.');
        toastMessage = "Upload failed";
        toastType = 'error';
        triggerToast(toastMessage, toastType);
        return;
      }

      if (!uploadResponse.ok) {
        console.error('Réponse non-ok de /upload', await uploadResponse.text());
        // return alert('Échec de l’upload (status ' + uploadResponse.status + ').');
        toastMessage = "Upload failed (status " + uploadResponse.status + ").";
        toastType = 'error';
        triggerToast(toastMessage, toastType);
        return;
      }

      const uploadJson = await uploadResponse.json();
      // On récupère le filename (UUID + .png)
      uploadedFilename = uploadJson.filename;
      console.log('Upload réussi, filename = ' + uploadedFilename + ', width = ' + uploadJson.width + ', height = ' + uploadJson.height);

      // === 2) Dès que l’upload est fait, on envoie le “play” ===
      try {
        // const playResponse = await fetch('http://localhost:8000/api/edition/visual/play', {
        const playResponse = await fetch('/api/edition/visual/play', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ media: uploadedFilename })
        });

        if (!playResponse.ok) {
          console.error('Réponse non-ok de /play', await playResponse.text());
          // return alert('Échec du Play (status ' + playResponse.status + ').');
          toastMessage = "Play failure (status " + uploadResponse.status + ").";
          toastType = 'error';
          triggerToast(toastMessage, toastType);
          return;
        }

        const playJson = await playResponse.json();
        console.log('Play command envoyé →', playJson);
      } catch (e) {
        console.error('Erreur réseau lors de /play :', e);
        // return alert('Échec de la commande Play.');
        toastMessage = "Play command failed";
        toastType = 'error';
        triggerToast(toastMessage, toastType);
        return;
      }

      // Passe en mode actif
      active = true;
    } else {
      // === 3) On était actif, on envoie donc le “stop” ===
      try {
        // const stopResponse = await fetch('http://localhost:8000/api/edition/visual/stop', {
        const stopResponse = await fetch('/api/edition/visual/stop', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
        });

        if (!stopResponse.ok) {
          console.error('Réponse non-ok de /stop', await stopResponse.text());
          // return alert('Échec du Stop (status ' + stopResponse.status + ').');
          toastMessage = "Stop failure (status " + stopResponse.status + ").";
          toastType = 'error';
          triggerToast(toastMessage, toastType);
          return;
        }

        const stopJson = await stopResponse.json();
        console.log('Stop command envoyé →', stopJson);
      } catch (e) {
        console.error('Erreur réseau lors de /stop :', e);
        // return alert('Échec de la commande Stop.');
        toastMessage = "Stop command failed";
        toastType = 'error';
        triggerToast(toastMessage, toastType);
        return;
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
      disabled={!uploadedFilename}
    >
      Save
    </button>
  </div>

  <SavePresetModal
    open={showModal}
    on:save={(e) => handleSavePreset(e.detail)}
    on:cancel={() => (showModal = false)}
  />

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
