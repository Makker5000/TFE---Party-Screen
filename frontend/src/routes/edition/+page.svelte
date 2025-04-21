<script>
    import Brightness from '$lib/components/Edition/Brightness.svelte';
    import DisplayVisual from '$lib/components/Edition/DisplayVisual.svelte';
    import QRCodeVote from '$lib/components/Edition/QRCodeVote.svelte';
    import RealTimeLyrics from '$lib/components/Edition/RealTimeLyrics.svelte';
    import DisplayingAds from '$lib/components/Edition/DisplayingAds.svelte';
</script>
  
  <svelte:head><title>Edition</title></svelte:head>
  
  <h1>Page Edition</h1>
  
  <!-- <Brightness brightness={brightnessValue} onChange={handleBrightnessChange} /> -->
  <Brightness />
  <DisplayVisual />
  <QRCodeVote />
  <RealTimeLyrics />
  <DisplayingAds />
  
<style>
    h1 { margin-bottom: 2rem; }
</style>