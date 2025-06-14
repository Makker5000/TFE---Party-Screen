<script>
  import Brightness from '$lib/components/Edition/Brightness.svelte';
  import DisplayVisual from '$lib/components/Edition/DisplayVisual.svelte';
  import QRCodeVote from '$lib/components/Edition/QRCodeVote.svelte';
  import RealTimeLyrics from '$lib/components/Edition/RealTimeLyrics.svelte';
  import DisplayingAds from '$lib/components/Edition/DisplayingAds.svelte';
  import { onMount } from 'svelte';
  import { isTokenExpired } from '$lib/utils/jwt';

  onMount(async () => {
    // Vérification de la Session avec le Token
    const token = localStorage.getItem('token');
    if (!token || isTokenExpired(token)) {
      alert('Session expirée, veuillez vous reconnecter.');
      localStorage.removeItem('token');
      window.location.href = '/login'; // ou utilise goto('/login') si tu veux éviter un reload complet
    }
  });
</script>

<svelte:head>
  <title>Edition</title>
</svelte:head>

<div class="min-h-screen bg-pink-50 flex flex-col items-center py-8 px-4">
  <h1 class="text-center text-black text-4xl font-bold mb-8">Page Edition</h1>

  <div class="w-full max-w-md space-y-6">
    <!-- Brightness Component -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title justify-center">Brightness</h2>
        <Brightness class="w-full" />
      </div>
    </div>

    <!-- Display Visual Component -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title justify-center">Display Visual</h2>
        <DisplayVisual class="w-full" />
      </div>
    </div>

    <!-- QR Code Vote Component -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title justify-center">QR Code Vote</h2>
        <QRCodeVote class="w-full" />
      </div>
    </div>

    <!-- Real-Time Lyrics Component -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title justify-center">Real-Time Lyrics</h2>
        <RealTimeLyrics class="w-full" />
      </div>
    </div>

    <!-- Displaying Ads Component -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title justify-center">Displaying Ads</h2>
        <DisplayingAds class="w-full" />
      </div>
    </div>
  </div>
</div>