<script>import '$app/environment';
import '../app.css';
import NavBar from '$lib/components/Navbar.svelte';
import { page } from '$app/stores';</script>
<!-- <script>
    import '$app/environment';
	import '../app.css';
    import NavBar from '$lib/components/NavBar.svelte';
    import { page } from '$app/stores';
</script>
  
{#if $page.url.pathname !== '/login'}
    <NavBar />
{/if}

<slot /> Affiche la page

<div class="flex flex-col min-h-screen items-center justify-center p-4">
	{#if $page.url.pathname !== '/login'}
		<NavBar />
	{/if}

	<slot />
</div> -->

<!-- _________________________________________________________________ -->

<!-- <script>
    import '../app.css';
    import NavBar from '$lib/components/NavBar.svelte';
    import { page } from '$app/stores';
</script>

<div class="flex flex-col min-h-screen items-center justify-center p-4">
    {#if $page.url.pathname !== '/login'}
        <NavBar />
    {/if}
    <slot />
</div> -->

<!-- _________________________________________________________________ -->



<div class="min-h-screen flex flex-col items-center px-4 bg-pink-50">
	{#if $page.url.pathname !== '/login'}
		<NavBar></NavBar>
	{/if}

	<!-- Page content centered horizontally -->
	<main class="w-full max-w-4xl mt-6">
		<slot></slot>
	</main>
</div>
