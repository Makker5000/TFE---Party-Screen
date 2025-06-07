<script lang="ts">
  import { onMount } from 'svelte';
  // liste initiale (tu pourras la remplacer dynamiquement ou la stocker dans un store)
  let tracks = Array.from({ length: 15 }, (_, i) => ({
    id: i + 1,
    title: `Titre #${i + 1}`,
    votes: 0
  }));

  // au clic sur un vote
  function vote(id: number) {
    tracks = tracks.map(t =>
      t.id === id ? { ...t, votes: t.votes + 1 } : t
    );
  }
</script>

<svelte:head>
  <title>Vote Music</title>
</svelte:head>

<div class="min-h-screen flex flex-col items-center py-12 px-4">
  <h1 class="text-5xl font-extrabold mb-8 text-primary">Vote pour ta track préférée</h1>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-4xl">
    {#each tracks as track}
      <div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow rounded-2xl">
        <div class="card-body flex flex-col items-center p-6">
          <h2 class="text-2xl font-semibold mb-4">{track.title}</h2>
          <button
            class="btn btn-accent mb-2 w-32"
            on:click={() => vote(track.id)}
          >
            Voter
          </button>
          <span class="text-lg">Votes : {track.votes}</span>
        </div>
      </div>
    {/each}
  </div>
</div>
