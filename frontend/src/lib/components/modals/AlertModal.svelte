<script lang="ts">
  export let show = false;
  export let title = 'Alerte';
  export let message = '';
  export let onClose = () => {};
</script>

{#if show}
  <div class="fixed  inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="card w-96 bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">{title}</h2>
        <p>{@html message.replace(/\n/g, '<br>')}</p>
        <div class="card-actions justify-end mt-4">
          <button class="btn btn-primary" on:click={onClose}>Close</button>
        </div>
      </div>
    </div>
  </div>
{/if}