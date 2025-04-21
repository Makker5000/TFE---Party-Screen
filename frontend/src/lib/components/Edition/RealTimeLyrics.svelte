<script>
    export let textColor = 'white';
    export let backgroundColor = 'black';
    export let font = 'Arial';
    export let animation = 'fade';
    export let availableColors = ['white', 'black', 'red', 'blue'];
    export let availableFonts = ['Arial', 'Times New Roman', 'Comic Sans MS'];
    export let availableAnimations = ['fade', 'slide', 'none'];

    async function playLyrics(textColor, backgroundColor, font, animation) {
      const config = {
        textColor: textColor,
        backgroundColor: backgroundColor,
        font: font,
        animation: animation
      };

      await fetch('http://localhost:8000/api/edition/lyrics/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      console.log(config);
    }

    async function stopLyrics() {
      await fetch('http://localhost:8000/api/edition/lyrics/stop', { method: 'POST' });
      console.log("Stop Real-time Lyrics Display");
    }
</script>
  
<div class="section">
    <h2>Real-time Lyrics Display</h2>
    <select bind:value={textColor}>
      {#each availableColors as color}
        <option>{color}</option>
      {/each}
    </select>
    <select bind:value={backgroundColor}>
      {#each availableColors as color}
        <option>{color}</option>
      {/each}
    </select>
    <select bind:value={font}>
      {#each availableFonts as f}
        <option>{f}</option>
      {/each}
    </select>
    <select bind:value={animation}>
      {#each availableAnimations as a}
        <option selected={a === 'fade'}>{a}</option>
      {/each}
    </select>
    <button on:click={() => playLyrics(textColor, backgroundColor, font, animation)}>Play</button>
    <button on:click={() => stopLyrics()}>Stop</button>
    <button>Save</button>
</div>