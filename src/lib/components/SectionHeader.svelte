<script>
  export let title;
  export let sub = '';
</script>

<div>
  <h2>{title}</h2>
  {#if sub}<p class="sub">{sub}</p>{/if}
</div>

<style>
  h2  { font-size:1.25rem; }
  .sub{ color:var(--muted); font-size:.875rem; margin-top:.2rem; }
</style>
