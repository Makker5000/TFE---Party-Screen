<script lang="ts">
  export let show = false;
  export let message = '';
  export let type: 'info' | 'success' | 'warning' | 'error' = 'info';
  export let duration = 5000; // en ms
  export let onClose = () => {};

  let timeout;

  $: if (show) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      onClose();
    }, duration);
  }
</script>

{#if show}
  <div class="toast toast-top toast-center z-50">
    <div class="alert"
      class:alert-info={type === 'info'}
      class:alert-success={type === 'success'}
      class:alert-warning={type === 'warning'}
      class:alert-error={type === 'error'}
    >
      <span>{message}</span>
      <button class="btn btn-sm btn-outline ml-2" on:click={onClose}>✕</button>
    </div>
  </div>
{/if}
