<script>
  export let brightness = 55;

  let currentBrightness = brightness;

  async function updateBrightness(val) {
    console.log("Brigthness value : ", val);
    await fetch('http://localhost:8000/api/edition/brightness', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brightness: val })
    });
  }

  function handleChange() {
    updateBrightness(currentBrightness);
  }
</script>

<div class="section">
  <h2>Brightness</h2>
  <input
    type="range"
    min="0"
    max="255"
    bind:value={currentBrightness}
    on:change={() => handleChange()} />
</div>

<style>
  .section { margin-bottom: 2rem; }
</style>