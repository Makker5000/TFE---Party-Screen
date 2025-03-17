<script>
import { writable } from 'svelte/store';

let message = writable('');

async function sendMessage() {
    const msg = { message: $message };

    try {
        const response = await fetch("http://127.0.0.1:8000/send_message/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(msg)
        });

        if (!response.ok){
            throw new Error(`Erreur Serveur: ${response.statusText}`);
        }

        const data = await response.json();
        console.log(data);  // Affiche la réponse du backend

    } catch (error) {
        console.error("Erreur d'envoi du message :", error);
    }
}
</script>

<main class="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
    <h1 class="text-4xl font-bold mb-4">Party Screen</h1>
    <input 
        class="p-2 text-black rounded-md" 
        bind:value={$message} 
        placeholder="Écris ton message..." />
    <button on:click={sendMessage} class="mt-4 p-2 bg-blue-500 rounded">Envoyer</button>
    <p class="mt-4 text-lg">Message: {$message}</p>
</main>

