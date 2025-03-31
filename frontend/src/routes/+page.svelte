<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  
  let message = writable('');
  let socket;
  let connected = false;
  let messages = [];
  
  // Modifier cette URL selon l'adresse de votre Raspberry Pi
  const BACKEND_WS_URL = 'ws://192.168.1.10/ws';
  
  function connect() {
    socket = new WebSocket(BACKEND_WS_URL);
    
    socket.addEventListener('open', () => {
      connected = true;
      console.log('Connecté au serveur WebSocket');
    });
    
    socket.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        messages = [...messages, data];
      } catch (error) {
        console.error('Erreur de parsing JSON:', error);
      }
    });
    
    socket.addEventListener('close', () => {
      connected = false;
      console.log('Déconnecté du serveur WebSocket');
      // Tentative de reconnexion après 3 secondes
      setTimeout(connect, 3000);
    });
    
    socket.addEventListener('error', (error) => {
      console.error('Erreur WebSocket:', error);
      connected = false;
    });
  }
  
  function sendMessage() {
    if (socket && socket.readyState === WebSocket.OPEN && $message) {
      socket.send($message);
      $message = '';
    }
  }
  
  onMount(() => {
    connect();
  });
  
  onDestroy(() => {
    if (socket) {
      socket.close();
    }
  });
</script>

<main class="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
  <h1 class="text-4xl font-bold mb-4">Party Screen</h1>
  
  <div class="mb-2 text-sm">
    Status: {connected ? 'Connecté' : 'Déconnecté'}
  </div>
  
  <input 
    class="p-2 text-black rounded-md w-64" 
    bind:value={$message} 
    placeholder="Écris ton message..." 
    on:keydown={(e) => e.key === 'Enter' && sendMessage()}
    disabled={!connected}
  />
  
  <button 
    on:click={sendMessage} 
    class="mt-4 p-2 bg-blue-500 rounded hover:bg-blue-600 transition-colors disabled:bg-gray-500"
    disabled={!connected || !$message}
  >
    Envoyer
  </button>
  
  {#if messages.length > 0}
    <div class="mt-6 w-64 max-h-48 overflow-y-auto">
      <h3 class="text-xl mb-2">Messages récents:</h3>
      <ul class="space-y-2">
        {#each messages as msg, i}
          <li class="p-2 rounded bg-gray-800">
            <span class={msg.status === 'Message envoyé' ? 'text-green-400' : 'text-red-400'}>
              {msg.status}:
            </span> 
            {msg.message}
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</main>
