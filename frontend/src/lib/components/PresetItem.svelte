<script>
  import { createEventDispatcher } from 'svelte';
  export let preset;
  const dispatch = createEventDispatcher();

  // Local active state toggle; preset.active can be provided
  let active = preset.active ?? false;

  function togglePlay() {
    active = !active;
    dispatch('playstop', { id: preset.id });
  }

  function deletePreset() {
    dispatch('delete', { id: preset.id });
  }

  function modifyPreset() {
    dispatch('modify', { id: preset.id });
  }
</script>

<div class="card bg-base-100 shadow-md">
  <div class="card-body">
    <!-- Preset Name -->
    <h2 class="card-title">{preset.name}</h2>
    <!-- Buttons -->
    <div class="flex justify-end space-x-2 mt-4">
      <!-- Play/Stop Toggle -->
      <button
        class="btn btn-square btn-outline btn-sm"
        class:btn-success={!active}
        class:btn-error={active}
        on:click={togglePlay}
      >
        {active ? '⏹️' : '▶️'}
      </button>
      <!-- Modify -->
      <button class="btn btn-outline btn-sm" on:click={modifyPreset}>
        ✏️
      </button>
      <!-- Delete -->
      <button class="btn btn-outline btn-sm btn-error" on:click={deletePreset}>
        🗑️
      </button>
    </div>
  </div>
</div>
