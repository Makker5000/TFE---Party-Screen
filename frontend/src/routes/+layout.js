// src/routes/+layout.js
// export const load = async ({ url }) => {
//     const checkSession = async (event) => {
//         return null; // ou return { user: null }; selon comment tu veux structurer
//       };
//     const isLoggedIn = checkSession(); // À faire toi-même

//     if (!isLoggedIn && url.pathname !== '/login') {
//         return {
//         status: 302,
//         redirect: '/login'
//         };
//     }

//     return {};
// };

export const load = async ({ url }) => {
  // mock : on ne vérifie pas vraiment la session pour l'instant
  const isLoggedIn = false; 

  // Si on est déjà sur /login, on ne fait rien (on veut afficher la page de login)
  if (url.pathname === '/login') {
    return {}; 
  }

  // Sinon, si pas connecté, on force vers /login
  if (!isLoggedIn) {
    return {
      status: 302,
      redirect: '/login'
    };
  }

  // (si connecté, on peut renvoyer une session fictive ou rien)
  return {};
};