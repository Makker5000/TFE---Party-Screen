<script>
	let musiques = [
		'Bohemian Rhapsody - Queen',
		'Imagine - John Lennon',
		'Smells Like Teen Spirit - Nirvana',
		'Billie Jean - Michael Jackson',
		'Like a Rolling Stone - Bob Dylan',
		'Hey Jude - The Beatles',
		'Hotel California - Eagles',
		'Shake It Off - Taylor Swift',
		'Blinding Lights - The Weeknd',
		'Rolling in the Deep - Adele'
	];

	let selection = '';
</script>

<h1 class="text-2xl font-bold mb-4">Sélectionne une musique</h1>

<select bind:value={selection} class="p-2 border rounded">
	<option value="" disabled selected>Choisir un titre</option>
	{#each musiques as titre}
		<option value={titre}>{titre}</option>
	{/each}
</select>

{#if selection}
	<p class="mt-4 text-lg">Tu as sélectionné : <strong>{selection}</strong></p>
{/if}

<style>
	select {
		width: 100%;
		max-width: 400px;
	}
</style>
