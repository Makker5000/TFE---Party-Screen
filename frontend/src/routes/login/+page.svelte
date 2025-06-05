<!-- <h1 class="text-2xl text-center my-8">Login</h1>
<div class="flex flex-col items-center gap-4">
  <input type="text" placeholder="Login" class="input input-bordered w-full max-w-xs" />
  <input type="password" placeholder="Mot de passe" class="input input-bordered w-full max-w-xs" />
  <button class="btn btn-primary w-full max-w-xs">Log in</button>
</div> -->

<!-- src/routes/login/+page.svelte -->
<script lang="ts">
  let username = '';
  let password = '';

  async function login(username: string, password: string) {
    try {
        // const res = await fetch('http://localhost:8000/api/users/login', {
        // // const res = await fetch('/api/users/login', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ username, password })
        // });

        // const res = await fetch('http://localhost:8000/api/users/login', {
        const res = await fetch('/api/users/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          // OAuth2PasswordRequestForm attend form-url-encoded, pas JSON :
          body: new URLSearchParams({
            username: username,
            password: password
          })
        })

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Échec de la connexion');
        }

        // Stocker le token
        localStorage.setItem('token', data.access_token);

        // Redirection vers /account
        window.location.href = '/settings';
    } catch (err) {
        console.error(err);
        alert(err.message);
    }

    // alert(`Tentative de connexion avec ${username}`);
  }
</script>

<svelte:head>
  <title>Login</title>
</svelte:head>

<style>
  /* ==========================
     1) Fond LED très sombre
     ========================== */
  .led-background {
    position: fixed;
    inset: 0; 
    background: rgba(0, 0, 0, 0.85); /* Noir opaque à 85 % pour un rendu très sombre */
    z-index: 0;
    overflow: hidden;
  }

  /* ==========================
     2) Conteneur TWAMPI en escalier
     ========================== */
.twampi-container {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;   /* verticalement centré */
  align-items: center;       /* horizontalement centré */
  padding: 1rem;
  pointer-events: none;
  user-select: none;
  z-index: 1;
}

  .twampi-container span {
    font-family: monospace;
    font-weight: bold;
    /* Très grande taille pour que T → I aillent presque du bord haut au bord bas */
    font-size: 15vh;                  
    line-height: 1;
    text-shadow:
      0 0 10px currentColor,
      0 0 20px currentColor,
      0 0 30px currentColor,
      0 0 40px currentColor;
    /* Chaque lettre gardera sa couleur (via classe) et aura un halo lumineux */
  }

  /* Couleurs 100 % opaques */
  .letter-t { color: #e63946; }   /* Rouge vif */
  .letter-w { color: #f4d35e; }   /* Jaune vif */
  .letter-a { color: #06d6a0; }   /* Vert vif */
  .letter-m { color: #118ab2; }   /* Bleu vif */
  .letter-p { color: #a23dff; }   /* Violet vif */
  .letter-i { color: #ff007f; }   /* Rose vif */

  /* ==========================
     3) Formulaire centré au-dessus
     ========================== */
  .container {
    position: relative;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2;                       /* Formulaire au-dessus de tout */
    padding: 3rem 1rem;               /* py-12 px-4 en Tailwind */
  }

  .transparent-card {
    background-color: rgba(0, 0, 0, 0.5); /* 80% opaque */
    backdrop-filter: blur(8px); /* léger flou derrière la carte */
  }
</style>

<!-- ========== FOND LED très sombre ========== -->
<div class="led-background">
  <!-- TWAMPI : on centre sur “M” grâce aux margin-left calculés -->
  <div class="twampi-container">
    <span class="letter-t" style="margin-left: -20vw;">T</span>
    <span class="letter-w" style="margin-left: -12vw;">W</span>
    <span class="letter-a" style="margin-left:  -4vw;">A</span>
    <span class="letter-m" style="margin-left:   4vw;">M</span>
    <span class="letter-p" style="margin-left:   12vw;">P</span>
    <span class="letter-i" style="margin-left:  20vw;">I</span>
  </div>
</div>

<!-- ========== FORMULAIRE DE LOGIN CENTRÉ ========== -->
<div class="container">
  <div class="relative z-10 w-full max-w-md">
    <div class="card bg-base-100 shadow-lg transparent-card">
      <div class="card-body space-y-6">
        <h2 class="card-title text-3xl text-center">Login</h2>

        <input
          type="text"
          placeholder="Username"
          bind:value={username}
          class="input input-bordered w-full"
        />

        <input
          type="password"
          placeholder="Password"
          bind:value={password}
          class="input input-bordered w-full"
        />

        <button class="btn btn-primary w-full mt-4" on:click={() => login(username, password)}>
          Login
        </button>
      </div>
    </div>
  </div>
</div>
