

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/0.BjXAXZiJ.js","_app/immutable/chunks/CRzFpERx.js","_app/immutable/chunks/DNWctpBc.js"];
export const stylesheets = ["_app/immutable/assets/0.viwVINn_.css"];
export const fonts = [];
