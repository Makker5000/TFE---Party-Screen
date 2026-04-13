// src/routes/+layout.js
import { browser } from '$app/environment';
import { redirect } from '@sveltejs/kit';

/**
 * Pas de SSR : la présence du JWT est lue dans localStorage, indisponible pendant le rendu serveur.
 * Sans cela, toute page protégée serait redirigée vers /login même avec un token valide.
 */
export const ssr = false;

export const load = async ({ url }) => {
	if (url.pathname === '/login') {
		return {};
	}

	if (browser) {
		const token = localStorage.getItem('token');
		if (!token) {
			redirect(302, '/login');
		}
	}

	return {};
};
