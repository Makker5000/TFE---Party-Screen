<!-- <script>
    import { goto } from '$app/navigation';
  
    const links = [
      { name: 'Settings', href: '/settings' },
      { name: 'Edit', href: '/edit' },
      { name: 'Presets', href: '/presets' },
      { name: 'Account', href: '/account' }
    ];
</script>
  
<nav class="nav-container">
  {#each links as link}
    <button on:click={() => goto(link.href)}>{link.name}</button>
  {/each}
</nav>
  
<style>
  .nav-container {
    display: flex;
    justify-content: space-around;
    background-color: #222;
    color: white;
    padding: 1rem;
    position: fixed;
    bottom: 0;
    width: 100%;
  }

  button {
    background: none;
    border: none;
    color: inherit;
    font-size: 1rem;
  }

  @media(min-width: 768px) {
    .nav-container {
      top: 0;
      bottom: auto;
    }
  }
</style> -->

<!-- _________________________________________________________________ -->

<!-- <script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  const pages = [
    { href: '/edit', icon: '✏️' },
    { href: '/settings', icon: '⚙️' },
    { href: '/presets', icon: '🔖' },
    { href: '/account', icon: '👤' },
  ];
</script>

<div class="btm-nav fixed bottom-0 w-full z-50">
  {#each pages as p}
    <button
      on:click={() => goto(p.href)}
      class={$page.url.pathname === p.href ? 'text-blue-500' : 'text-black'}>
      <span>{p.icon}</span>
    </button>
  {/each}
</div> -->

<!-- _________________________________________________________________ -->

<!-- <script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	const pages = [
		{ href: '/edit', icon: '✏️' },
		{ href: '/settings', icon: '⚙️' },
		{ href: '/presets', icon: '🔖' },
		{ href: '/account', icon: '👤' },
	];
</script>

<div class="btm-nav fixed bottom-0 w-full z-50 bg-base-100">
	{#each pages as p}
		<button
			class="text-3xl"
			on:click={() => goto(p.href)}>
			<span class={$page.url.pathname === p.href ? 'text-primary' : 'text-neutral'}>
				{p.icon}
			</span>
		</button>
	{/each}
</div> -->

<!-- _________________________________________________________________ -->

<!-- <script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	const pages = [
		{ href: '/edit', icon: '✏️' },
		{ href: '/settings', icon: '⚙️' },
		{ href: '/presets', icon: '🔖' },
		{ href: '/account', icon: '👤' },
	];
</script>

<div class="fixed bottom-0 w-full z-50 bg-white dark:bg-gray-900 shadow-md flex justify-around py-2">
	{#each pages as p}
		<button
			class="text-3xl"
			on:click={() => goto(p.href)}>
			<span class={$page.url.pathname === p.href ? 'text-blue-600' : 'text-gray-500'}>
				{p.icon}
			</span>
		</button>
	{/each}
</div> -->

<!-- _________________________________________________________________ -->

<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	const pages = [
    { href: '/settings', icon: '⚙️' },
		{ href: '/edition', icon: '✏️' },
		{ href: '/presets', icon: '🔖' },
		{ href: '/account', icon: '👤' },
	];
</script>

<nav class="fixed top-0 left-0 w-full bg-white border-b shadow z-50">
	<div class="flex justify-center gap-6 py-3">
		{#each pages as p}
			<button
				class="text-3xl hover:text-blue-500 transition-colors"
				on:click={() => goto(p.href)}
			>
				<span class={$page.url.pathname === p.href ? 'text-blue-600' : 'text-gray-500'}>
					{p.icon}
				</span>
			</button>
		{/each}
	</div>
</nav>
