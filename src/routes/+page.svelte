<!-- <script lang="ts">
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
</div> -->


<!-- ------------------- Page mise à jour -------------- -->
<script lang="ts">
  // ta logique reste la même
  let tracks = Array.from({ length: 15 }, (_, i) => ({
    id: i + 1,
    title: `Titre #${i + 1}`,
    votes: 0
  }));

  function vote(id: number) {
    tracks = tracks.map(t =>
      t.id === id ? { ...t, votes: t.votes + 1 } : t
    );
  }
</script>

<svelte:head>
  <title>Vote for your favorite song</title>
</svelte:head>

<div class="min-h-screen flex flex-col items-center py-12 px-4 bg-gray-800">
  <!-- Titre de la page -->
  <h1 class="text-5xl font-extrabold mb-8 text-white">Vote for your favorite song</h1>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-4xl">
    {#each tracks as track}
      <div class="card bg-gray-900 text-white shadow-lg hover:shadow-xl transition-shadow rounded-2xl">
        <div class="card-body flex flex-col items-center p-6">
          <!-- Numéro avant le titre -->
          <h2 class="text-2xl font-semibold mb-4 flex items-baseline">
            <span class="text-blue-500 font-extrabold mr-2">#{track.id}</span>
            <span>{track.title}</span>
          </h2>

          <!-- Bouton personnalisé -->
          <button
            class="btn border-2 border-blue-500 text-blue-500 bg-transparent hover:bg-blue-500 hover:text-white mb-2 w-32 transition-colors rounded-lg"
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
