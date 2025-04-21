<script>
    export let url = '';
    // export let defaultUrl = 'https://default.url';
    export let defaultUrl = '';

    async function generateQRCode(url) {
        await fetch('http://localhost:8000/api/edition/qrcode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url || defaultUrl
            })
        });
    }

    async function playQrCode(){
        await fetch('http://localhost:8000/api/edition/qrcode/play', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: "play"
            })
        });
    }

    async function stopQrCode(){
        await fetch('http://localhost:8000/api/edition/qrcode/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: "stop"
            })
        });
    }
</script>
  
<div class="section">
   <h2>QR Code Vote</h2>
   <input type="text" bind:value={url} placeholder="Enter URL..." />
   <button on:click={() => generateQRCode(url || defaultUrl)}>Générer QR Code</button>
   <button on:click={() => playQrCode()} >Play</button>
   <button on:click={() => stopQrCode()}>Stop</button>
   <button>Save</button>
</div>
