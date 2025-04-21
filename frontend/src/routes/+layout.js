// src/routes/+layout.js
export const load = async ({ url }) => {
    const checkSession = async (event) => {
        return null; // ou return { user: null }; selon comment tu veux structurer
      };
    const isLoggedIn = checkSession(); // À faire toi-même

    if (!isLoggedIn && url.pathname !== '/login') {
        return {
        status: 302,
        redirect: '/login'
        };
    }

    return {};
};