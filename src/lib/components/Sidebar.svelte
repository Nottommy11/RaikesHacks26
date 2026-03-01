<script>
  export let profile;
  export let role;
  export let uid    = '';
  export let active = '';
</script>

<aside>
  <div class="logo">
    <span class="n">N</span>
    <span class="name">1984 But Good</span>
  </div>

  <div class="profile-block">
    <div class="avatar">
      {#if role === 'student'}
        {profile.first_name[0]}{profile.last_name[0]}
      {:else}
        {profile.username?.[0]?.toUpperCase() ?? 'A'}
      {/if}
    </div>
    <div>
      {#if role === 'student'}
        <strong>{profile.first_name} {profile.last_name}</strong>
        <small>{profile.nuid}</small>
      {:else}
        <strong>{profile.username}</strong>
        <small>{profile.admin_type}</small>
      {/if}
    </div>
  </div>

  {#if role === 'admin'}
    <div class="role-badge">Admin View</div>
  {/if}

  <nav>
    {#if role === 'student'}
      <a href="/student?uid={uid}"           class="nav-link" class:active={active==='dashboard'}>Dashboard</a>
      <a href="/student/interests?uid={uid}" class="nav-link" class:active={active==='interests'}>My Interests</a>
    {:else}
      <a href="/admin"           class="nav-link" class:active={active==='overview'}>Overview</a>
    {/if}
  </nav>

  {#if role === 'admin'}
    <div class="anon-note">
      All data is anonymous. No individual student records are accessible here.
    </div>
  {/if}

  <a href="/login" class="signout">← Switch account</a>
</aside>

<style>
  aside {
    background: var(--ink);
    color: #fff;
    padding: 1.75rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 230px;
    flex-shrink: 0;
    min-height: 100vh;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
  }

  .logo { display: flex; align-items: center; gap: .6rem; }
  .n {
    width: 32px; height: 32px; background: var(--red);
    border-radius: 7px; display: flex; align-items: center;
    justify-content: center; font-family: var(--font-display);
    font-size: 1.1rem; font-weight: 700; flex-shrink: 0;
  }
  .name { font-family: var(--font-display); font-size: .95rem; font-weight: 700; line-height: 1.2; }

  .profile-block {
    display: flex; align-items: center; gap: .65rem;
    padding: .85rem; background: rgba(255,255,255,.07); border-radius: 10px;
  }
  .avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--red); display: flex; align-items: center;
    justify-content: center; font-weight: 700; font-size: .85rem; flex-shrink: 0;
  }
  .profile-block strong { display: block; font-size: .85rem; line-height: 1.3; }
  .profile-block small  { color: rgba(255,255,255,.45); font-size: .72rem; }

  .role-badge {
    display: inline-block; padding: .25rem .7rem;
    background: rgba(208,0,0,.2); border: 1px solid rgba(208,0,0,.4);
    border-radius: 999px; font-size: .72rem; font-weight: 600;
    color: #f88; letter-spacing: .05em; text-transform: uppercase; width: fit-content;
  }

  nav { display: flex; flex-direction: column; gap: .15rem; }
  .nav-link {
    padding: .5rem .8rem; border-radius: 7px;
    color: rgba(255,255,255,.55); font-size: .85rem;
    font-weight: 500; text-decoration: none; transition: all .15s;
  }
  .nav-link:hover, .nav-link.active {
    background: rgba(255,255,255,.1); color: #fff; text-decoration: none;
  }

  .anon-note {
    background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1);
    border-radius: 8px; padding: .7rem; font-size: .72rem;
    color: rgba(255,255,255,.35); line-height: 1.5;
  }

  .signout {
    margin-top: auto; font-size: .78rem; color: rgba(255,255,255,.35);
    text-decoration: none; padding: .45rem .8rem;
    border-radius: 7px; transition: all .15s;
  }
  .signout:hover { color: rgba(255,255,255,.6); background: rgba(255,255,255,.06); text-decoration: none; }
</style>
