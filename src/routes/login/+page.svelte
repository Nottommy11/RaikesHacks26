<script>
  import { goto } from '$app/navigation';
  export let data;

  let mode       = 'student';  // 'student' | 'admin'
  let selectedId = '';

  function login() {
    if (!selectedId) return;
    if (mode === 'student') {
      goto(`/student?uid=${selectedId}`);
    } else {
      goto(`/admin?aid=${selectedId}`);
    }
  }
</script>

<div class="page">
  <div class="left">
    <div class="brand">
      <span class="n">N</span>
      <div class="brand-text">
        <strong>1984 But Good</strong>
        <span>University of Nebraska–Lincoln</span>
      </div>
    </div>
    <blockquote>
      "Where your campus data<br>
      <em>works for you.</em>"
    </blockquote>
  </div>

  <div class="right">
    <div class="card login-card">
      <h2>Sign in</h2>
      <p class="hint">This is a demo — pick any account to explore.</p>

      <div class="tabs">
        <button class:active={mode === 'student'} on:click={() => { mode='student'; selectedId=''; }}>
          Student
        </button>
        <button class:active={mode === 'admin'} on:click={() => { mode='admin'; selectedId=''; }}>
          Admin / Staff
        </button>
      </div>

      {#if mode === 'student'}
        <label>
          <span>Select a student</span>
          <select bind:value={selectedId}>
            <option value="">— choose —</option>
            {#each data.users as u}
              <option value={u.user_id}>
                {u.last_name}, {u.first_name} &nbsp;·&nbsp; {u.nuid}
              </option>
            {/each}
          </select>
        </label>
      {:else}
        <label>
          <span>Select an admin</span>
          <select bind:value={selectedId}>
            <option value="">— choose —</option>
            {#each data.admins as a}
              <option value={a.admin_id}>
                {a.username} &nbsp;·&nbsp; {a.admin_type}
              </option>
            {/each}
          </select>
        </label>
      {/if}

      <button class="btn-login" on:click={login} disabled={!selectedId}>
        Enter Dashboard →
      </button>
    </div>
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  /* ── Left panel ── */
  .left {
    background: var(--red);
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 4rem;
    color: #fff;
    position: relative;
    overflow: hidden;
  }
  .left::after {
    content: '';
    position: absolute;
    bottom: -80px; right: -80px;
    width: 320px; height: 320px;
    border-radius: 50%;
    background: rgba(255,255,255,.06);
  }
  .left::before {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 240px; height: 240px;
    border-radius: 50%;
    background: rgba(255,255,255,.04);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 3rem;
  }
  .n {
    font-family: var(--font-display);
    font-size: 3.5rem;
    font-weight: 700;
    width: 64px; height: 64px;
    background: #fff;
    color: var(--red);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    flex-shrink: 0;
  }
  .brand-text strong {
    display: block;
    font-family: var(--font-display);
    font-size: 1.8rem;
    color: #fff;
  }
  .brand-text span {
    font-size: .8rem;
    opacity: .75;
    letter-spacing: .04em;
  }

  blockquote {
    font-family: var(--font-display);
    font-size: 2rem;
    line-height: 1.3;
    color: rgba(255,255,255,.9);
    border: none;
    padding: 0;
  }
  blockquote em {
    font-style: italic;
    color: #fff;
  }

  /* ── Right panel ── */
  .right {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    background: var(--cream);
  }

  .login-card {
    width: 100%;
    max-width: 420px;
  }
  .login-card h2 {
    font-size: 1.8rem;
    margin-bottom: .25rem;
  }
  .hint {
    color: var(--muted);
    font-size: .85rem;
    margin-bottom: 1.5rem;
  }

  .tabs {
    display: flex;
    gap: .5rem;
    margin-bottom: 1.25rem;
    border-bottom: 2px solid var(--border);
    padding-bottom: .75rem;
  }
  .tabs button {
    background: none;
    border: none;
    cursor: pointer;
    font-family: var(--font-sans);
    font-size: .9rem;
    color: var(--muted);
    padding: .35rem .75rem;
    border-radius: 6px;
    font-weight: 500;
    transition: all .15s;
  }
  .tabs button.active {
    background: var(--red);
    color: #fff;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: .4rem;
    margin-bottom: 1.25rem;
  }
  label span {
    font-size: .82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: var(--muted);
  }
  select {
    font-family: var(--font-sans);
    font-size: .95rem;
    padding: .65rem .85rem;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: var(--surface);
    color: var(--ink);
    cursor: pointer;
    outline: none;
    transition: border-color .15s;
  }
  select:focus { border-color: var(--red); }

  .btn-login {
    width: 100%;
    padding: .85rem;
    background: var(--red);
    color: #fff;
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background .15s, transform .1s;
    letter-spacing: .02em;
  }
  .btn-login:hover:not(:disabled) { background: var(--red-dark); transform: translateY(-1px); }
  .btn-login:disabled { opacity: .45; cursor: not-allowed; }

  @media (max-width: 720px) {
    .page { grid-template-columns: 1fr; }
    .left { padding: 2.5rem; min-height: 220px; }
    blockquote { font-size: 1.4rem; }
  }
</style>
