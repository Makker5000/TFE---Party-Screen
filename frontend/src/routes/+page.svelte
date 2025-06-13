<!-- Last version -->
<script lang="ts">
  import { onMount } from 'svelte';

  type Track = {
    track_id: number;
    title: string;
    artist: string;
    votes: number;
  };

  let tracks: Track[] = [];

  let token: string;

  function isTokenValid(token: string): boolean {
    try {
      const payloadBase64 = token.split('.')[1];
      const payloadJson = atob(payloadBase64);
      const payload = JSON.parse(payloadJson);
      const exp = payload.exp;
      const now = Math.floor(Date.now() / 1000);
      return exp && now < exp;
    } catch (err) {
      console.warn('Token invalid or corrupt');
      return false;
    }
  }

  async function getOrRefreshToken(): Promise<string> {
    console.log("On rentre dans la fonction pour refresh token");
    const stored = localStorage.getItem('token');
    if (stored && isTokenValid(stored)) {
      return stored;
    }

    const response = await fetch('http://localhost:8000/api/login', {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Login failed');
    const tokenData = await response.json();
    const newToken = tokenData.token;
    localStorage.setItem('token', newToken);
    return newToken;
  }

  onMount(async () => {    
    try {
      token = await getOrRefreshToken();

      const res = await fetch('http://localhost:8000/api/tracks', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        },
      });
      // const res = await fetch('/api/tracks');
      const data = await res.json();
      tracks = data.map((t: any) => ({ ...t, votes: 0 }));
    } catch (e) {
      console.error('Erreur chargement tracks:', e);
    }
  });

  async function vote(id: number) {
    try {
      const res = await fetch(`http://localhost:8000/api/vote/${id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
      });
      // const res = await fetch(`/api/vote/${id}`, { method: 'POST' });
      if (!res.ok) throw new Error('Vote refusé');
      tracks = tracks.map(t =>
        t.track_id === id ? { ...t, votes: t.votes + 1 } : t
      );
    } catch (e) {
      alert(e.message);
    }
  }
</script>

<svelte:head>
  <title>Vote for your favorite song</title>
</svelte:head>

<div class="min-h-screen flex flex-col items-center py-12 px-4 bg-gray-700">
  <h1 class="text-5xl font-extrabold mb-8 text-white">Vote for your favorite song</h1>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-4xl">
    {#each tracks as t}
      <div class="card bg-gray-900 text-white shadow-lg hover:shadow-xl transition-shadow rounded-2xl">
        <div class="card-body flex flex-col items-center p-6">
          <h2 class="text-2xl font-semibold mb-2 flex items-center">
            <!-- Bulle sombre autour du numéro -->
            <span class="bg-gray-800 rounded-full px-3 py-1 text-sm font-extrabold text-white mr-3">
              {t.track_id}.
            </span>
            <span>{t.title}</span>
          </h2>
          <h3 class="text-1xl font-semibold mb-4 flex items-center ">
            <span>{t.artist}</span>
          </h3>

          <button
            class="btn border-2 border-blue-500 text-blue-500 bg-transparent hover:bg-blue-500 hover:text-white mb-2 w-32 transition-colors rounded-lg"
            on:click={() => vote(t.track_id)}
          >
            Voter
          </button>

          <span class="text-lg">Votes : {t.votes}</span>
        </div>
      </div>
    {/each}
  </div>
</div>