export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["favicon.png"]),
	mimeTypes: {".png":"image/png"},
	_: {
		client: {start:"_app/immutable/entry/start.D5i9ssFt.js",app:"_app/immutable/entry/app.DUCp07ut.js",imports:["_app/immutable/entry/start.D5i9ssFt.js","_app/immutable/chunks/CjeVcDcG.js","_app/immutable/chunks/DNWctpBc.js","_app/immutable/chunks/Cjp44n09.js","_app/immutable/entry/app.DUCp07ut.js","_app/immutable/chunks/DNWctpBc.js","_app/immutable/chunks/CrMCGlBk.js","_app/immutable/chunks/CRzFpERx.js","_app/immutable/chunks/Cjp44n09.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js'))
		],
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
