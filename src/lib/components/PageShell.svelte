<script>
  import Sidebar from './Sidebar.svelte';
  export let profile;
  export let role;
  export let uid    = '';
  export let active = '';
</script>

<div class="shell">
  <Sidebar {profile} {role} {uid} {active} />
  <main>
    <slot />
  </main>
</div>

<style>
  .shell {
    display: flex;
    min-height: 100vh;
    width: 100%;
  }
  main {
    flex: 1;
    min-width: 0;
    padding: 2.25rem 2.5rem;
    display: flex;
    flex-direction: column;
    gap: 2.25rem;
  }
  @media (max-width: 860px) {
    .shell { flex-direction: column; }
    main { padding: 1.5rem; }
  }
</style>
