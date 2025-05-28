<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let open = false;

  const dispatch = createEventDispatcher();

  let presetName = '';

  function handleSave() {
    if (presetName.trim() === '') return;
    dispatch('save', presetName.trim());
    presetName = '';
  }

  function handleCancel() {
    presetName = '';
    dispatch('cancel');
  }
</script>

{#if open}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-md w-full max-w-md">
      <h2 class="text-lg font-semibold mb-4 text-black">Save a Preset</h2>

      <input
        type="text"
        bind:value={presetName}
        placeholder="Name of the Preset..."
        class="w-full px-4 py-2 border rounded mb-4"
      />

      <div class="flex justify-end space-x-2">
        <button
          class="bg-gray-300 hover:bg-gray-400 text-black px-4 py-2 rounded"
          on:click={handleCancel}
        >
          Annuler
        </button>
        <button
          class="bg-blue-800 hover:bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-100"
          on:click={handleSave}
          disabled={presetName.trim() === ''}
        >
          Sauvegarder
        </button>
      </div>
    </div>
  </div>
{/if}
