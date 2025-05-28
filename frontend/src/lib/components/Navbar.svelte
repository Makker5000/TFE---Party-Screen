<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';

  const pages = [
    { href: '/settings', icon: '⚙️' },
    { href: '/edition',  icon: '✏️' },
    { href: '/presets',  icon: '🔖' },
    { href: '/account',  icon: '👤' },
  ];

  // Animations
  let underlineX     = tweened(0, { duration: 300, easing: cubicOut });
  let underlineWidth = tweened(0, { duration: 300, easing: cubicOut });

  // Référence au conteneur des boutons
  let containerEl;

  function updateCursor() {
    if (typeof document === 'undefined' || !containerEl) return;
    const btns = containerEl.querySelectorAll('.nav-btn');
    const idx  = pages.findIndex(p => p.href === $page.url.pathname);
    const el   = btns[idx];
    if (el) {
      const parentRect = containerEl.getBoundingClientRect();
      const elRect = el.getBoundingClientRect();
      underlineX.set(elRect.left - parentRect.left);
      underlineWidth.set(elRect.width);
    }
  }

  // Met à jour au changement de page
  $: $page, setTimeout(updateCursor, 0);

  onMount(() => {
    updateCursor();
    window.addEventListener('resize', updateCursor);
  });
</script>

<style>
  @media (max-width: 640px) {
    nav { top: auto; bottom: 0; }
  }
</style>

<nav class="fixed top-0 left-0 w-full z-50">
  <div class="mx-auto max-w-md">
    <div class="card bg-white shadow-md">
      <!-- Container pour référence et positionnement relatif -->
      <div class="relative flex justify-around py-3" bind:this={containerEl}>
        {#each pages as p}
          <button
            class="nav-btn text-3xl hover:text-blue-500 transition-colors"
            on:click={() => goto(p.href)}
          >
            <span class={$page.url.pathname === p.href ? 'text-blue-600' : 'text-gray-500'}>
              {p.icon}
            </span>
          </button>
        {/each}

        <!-- Curseur animé -->
        <div
          class="absolute bottom-0 left-0 h-1 bg-blue-500 rounded transition-all duration-300"
          style="transform: translateX({$underlineX}px); width: {$underlineWidth}px;"
        ></div>
      </div>
    </div>
  </div>
</nav>
