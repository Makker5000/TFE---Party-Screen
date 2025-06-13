// import adapter from '@sveltejs/adapter-vercel';
// import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

// const config = {
// 	preprocess: vitePreprocess(),
// 	kit: { adapter: adapter() }
// };

// export default config;

// ----------------------------------------------------

// frontend/svelte.config.js
import vercel from '@sveltejs/adapter-vercel';
import preprocess from 'svelte-preprocess';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: preprocess(),

  kit: {
    adapter: vercel(),
    // si tu avais un `paths.base`, tu peux l’enlever ici
  }
};

export default config;
