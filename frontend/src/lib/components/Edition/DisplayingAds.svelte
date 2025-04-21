<script>
    export let textColor = 'white';
    export let backgroundColor = 'black';
    export let font = 'Arial';
    export let animation = 'scroll';
    export let speed = 1;
    export let content = '';
    export let availableColors = ['white', 'black', 'yellow'];
    export let availableFonts = ['Arial', 'Verdana'];
    export let availableAnimations = ['scroll', 'bounce', 'none'];

    async function playAds(textColor, backgroundColor, font, animation, speed, content) {
      const config = {
        textColor: textColor,
        backgroundColor: backgroundColor,
        font: font,
        animation: animation,
        speed: speed,
        content: content,
        state: "play"
      };

      await fetch('http://localhost:8000/api/edition/ads/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
    }

    async function stopAds() {
      const config = {
        textColor: '',
        backgroundColor: '',
        font: '',
        animation: '',
        speed: 0,
        content: '',
        state: "stop"
      };

      await fetch('http://localhost:8000/api/edition/ads/stop', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      console.log("Stop Displaying Ads");
    }
</script>
  
<div class="section">
    <h2>Displaying Ads</h2>
    <select bind:value={textColor}>
      {#each availableColors as color}<option>{color}</option>{/each}
    </select>
    <select bind:value={backgroundColor}>
      {#each availableColors as color}<option>{color}</option>{/each}
    </select>
    <select bind:value={font}>
      {#each availableFonts as f}<option>{f}</option>{/each}
    </select>
    <select bind:value={animation}>
      {#each availableAnimations as a}<option selected={a === 'scroll'}>{a}</option>{/each}
    </select>
    <input type="range" min="0.1" max="5" step="0.1" bind:value={speed} />
    <input type="text" placeholder="Enter ad message" bind:value={content} />
    <button on:click={() => playAds(textColor, backgroundColor, font, animation, speed, content)}>Play</button>
    <button on:click={() => stopAds()}>Stop</button>
    <button>Save</button>
</div>