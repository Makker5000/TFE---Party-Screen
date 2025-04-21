<script>
	import { writable } from 'svelte/store';

	export let power = false;
	export let screenCount = '';
	export let matrixCount = '';
	export let screenShape = '';

	export const screenShapes = ["Square", "Grid", "Line", "Pyramid", "Circle"];

	// Envoie immédiat pour Power
	async function updatePower(state) {
		console.log(state);
		await fetch('http://localhost:8000/api/settings/power', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ power: state })
		});
	}

	// Envoie du Formulaire
	async function submitSettings(screenCount, matrixCount, screenShape) {
		const payload = {
			screenCount: screenCount,
			matrixCount: matrixCount,
			screenShape: screenShape
		};

		await fetch('http://localhost:8000/api/settings/config', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
	}


</script>

<svelte:head><title>Settings</title></svelte:head>

<h1 class="text-2xl">Page Screen Settings</h1>
<!-- Formulaire principal -->
<div class="flex flex-col gap-6 mt-4 max-w-md w-full mx-auto">
	<!-- Power -->
	<section class="border rounded-xl p-4 shadow-sm bg-gray-100">
		<h2 class="text-lg font-semibold mb-2">Power on / off</h2>
		<input
			type="checkbox"
			class="w-5 h-5"
			bind:checked={power}
			on:change={() => updatePower(power)}
		/>
	</section>

	<!-- Number of Screen -->
	<section class="border rounded-xl p-4 shadow-sm bg-gray-100">
		<h2 class="text-lg font-semibold mb-2">Number of Screen</h2>
		<input
			type="number"
			min="0"
			max="10"
			class="border p-2 rounded w-full"
			bind:value={screenCount}
		/>
	</section>

	<!-- Number of Matrix -->
	<section class="border rounded-xl p-4 shadow-sm bg-gray-100">
		<h2 class="text-lg font-semibold mb-2">Number of Matrix</h2>
		<input
			type="number"
			min="0"
			max="10"
			class="border p-2 rounded w-full"
			bind:value={matrixCount}
			disabled={!screenCount || Number(screenCount) === 0}
		/>
	</section>

	<!-- Screen Shape -->
	<section class="border rounded-xl p-4 shadow-sm bg-gray-100">
		<h2 class="text-lg font-semibold mb-2">Screen Shape</h2>
		<select
			class="border p-2 rounded w-full"
			bind:value={screenShape}
			disabled={!screenCount || Number(screenCount) === 0}
		>
			{#each screenShapes as shape}
				<option value={shape}>{shape}</option>
			{/each}
		</select>
	</section>

	<!-- Submit All -->
	<button
		class="mt-4 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
		on:click={() => submitSettings(screenCount, matrixCount, screenShape)}
	>
		Apply
	</button>
</div>
