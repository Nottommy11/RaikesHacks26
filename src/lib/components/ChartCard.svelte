<script>
  export let label = '';
  export let wide  = false;
  export let wide2 = false;
</script>

<div class="chart-card" class:wide class:wide2>
  {#if label}<div class="chart-label">{label}</div>{/if}
  <slot />
</div>

<style>
  .chart-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.35rem 1.5rem; box-shadow: var(--shadow); min-width: 0;
  }
  .wide { grid-column: span 2; }
  .chart-label { font-size:.74rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin-bottom:.85rem; }
  .wide2 { grid-column: span 2; }
  @media (max-width:700px) { .wide { grid-column: span 1; } }
</style>
