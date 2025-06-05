<script lang="ts">
  import { onMount } from 'svelte';

  let username = '';
  let password = '';
  let email = '';

  let oldPassword = '';
  let newPassword = '';
  let newUsername = '';

  let token: string;

  onMount(() => {
    token = localStorage.getItem('token') ?? '';
  });
  
  async function updateUsername(newUsername: string) {
    // Appel API ou logique de mise à jour
    try {
        // const res = await fetch('http://localhost:8000/api/users/username', {
        const res = await fetch('/api/users/username', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` // à adapter selon ta gestion
            },
            body: JSON.stringify({ new_username: newUsername })
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Erreur lors du changement de nom');
        }

        const data = await res.json();
        alert(data.message);
    } catch (err) {
        console.error(err);
        alert(err.message);
    }

    // alert(`Username mis à jour : ${username}`);
  }

  async function updatePassword(currentPassword: string, newPassword: string) {
    // Appel API ou logique de mise à jour
    try {
        // const res = await fetch('http://localhost:8000/api/users/password', {
        const res = await fetch('/api/users/password', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Erreur lors du changement de mot de passe');
        }

        const data = await res.json();
        alert(data.message);
    } catch (err) {
        console.error(err);
        alert(err.message);
    }

    // alert(`Mot de passe mis à jour : ${password}`);
  }

  async function createAccount(username: string, email: string, password: string) {
    // Appel API ou logique de création
    try {
        // const res = await fetch('http://localhost:8000/api/users/register', {
        const res = await fetch('/api/users/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Erreur lors de l\'inscription');
        }

        alert(data.message);
        // Rediriger vers login si tout va bien
        window.location.href = '/login';
    } catch (err) {
        console.error(err);
        alert(err.message);
    }

    // alert(`Compte créé pour : ${newUsername}`);
  }

  async function logout() {
    // Déconnexion
    try {
        // const res = await fetch('http://localhost:8000/api/users/logout', {
        const res = await fetch('/api/users/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Erreur lors de la déconnexion');
        }

        // Nettoyer le token du localStorage ou cookie
        localStorage.removeItem('token');
        window.location.href = '/login';
    } catch (err) {
        console.error(err);
        alert(err.message);
    }

    // alert('Déconnexion effectuée');
  }

  async function deleteAccount() {
    // Suppression du compte
    // if (confirm("Confirmer la suppression du compte ?")) {
    //   alert('Compte supprimé');
    // }

    if (!confirm("Es-tu sûr de vouloir supprimer ton compte ?")) return;

    try {
        // const res = await fetch('http://localhost:8000/api/users/delete', {
        const res = await fetch('/api/users/delete', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Erreur lors de la suppression');
        }

        const data = await res.json();
        alert(data.message);
        // Rediriger vers page de login
        window.location.href = '/login';
    } catch (err) {
        console.error(err);
        alert(err.message);
    }

  }
</script>

<svelte:head>
  <title>Account</title>
</svelte:head>

<div class="min-h-screen bg-pink-50 flex flex-col items-center py-8 px-4">
  <h1 class="text-center text-black text-4xl font-bold mb-8">Account</h1>

  <div class="w-full max-w-md space-y-6">

    <!-- Modifier Username -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title">Change Username</h2>
        <input
          type="text"
          placeholder="New Username"
          bind:value={newUsername}
          class="input input-bordered w-full"
        />
        <button class="btn btn-primary mt-4" on:click={() => updateUsername(username)}>Update</button>
      </div>
    </div>

    <!-- Modifier Password -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title">Change Password</h2>
        <input
          type="password"
          placeholder="Old Password"
          bind:value={oldPassword}
          class="input input-bordered w-full"
        />
        <input
          type="password"
          placeholder="New Password"
          bind:value={newPassword}
          class="input input-bordered w-full"
        />
        <button class="btn btn-primary mt-4" on:click={() => updatePassword(oldPassword, newPassword)}>Update</button>
      </div>
    </div>

    <!-- Créer un compte -->
    <div class="card bg-base-100 shadow-md mx-auto">
      <div class="card-body">
        <h2 class="card-title">Create New Account</h2>
        <input
          type="text"
          placeholder="Username"
          bind:value={username}
          class="input input-bordered w-full"
          required
        />
        <input
          type="email"
          placeholder="E-mail"
          bind:value={email}
          class="input input-bordered w-full"
          required
        />
        <input
          type="password"
          placeholder="Password"
          bind:value={password}
          class="input input-bordered w-full"
          required
        />
        <button class="btn btn-success mt-4" on:click={() => createAccount(username, email, password)}>Create Account</button>
      </div>
    </div>

    <!-- Déconnexion & Suppression -->
    <div class="flex flex-col space-y-4 items-center">
      <button class="btn btn-warning w-full max-w-xs" on:click={logout}>Log out</button>
      <button class="btn btn-error w-full max-w-xs" on:click={deleteAccount}>Delete Account</button>
    </div>

  </div>
</div>
