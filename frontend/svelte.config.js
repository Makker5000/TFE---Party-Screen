import adapter from '@sveltejs/adapter-vercel';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
	preprocess: vitePreprocess(),
	kit: { adapter: adapter() }
};

export default config;

// ----------------------------------------------------
// import adapter from '@sveltejs/adapter-static';
// import preprocess from 'svelte-preprocess';

// /** @type {import('@sveltejs/kit').Config} */
// const config = {
//   preprocess: preprocess(),
//   kit: {
//     adapter: adapter({
//       // genere tout dans 'public'
//       pages: 'public',
//       assets: 'public',
//       fallback: null
//     }),
//     // si ton projet n’est pas à la racine, tu peux préciser `paths.base`
//   }
// };

// export default config;
