<script>
  export let label;
  export let value;
  export let sub   = '';
  export let color = '';
</script>

<div class="stat-card">
  <div class="label">{label}</div>
  <div class="value" style={color ? `color:var(--${color})` : ''}>{value}</div>
  {#if sub}<div class="sub">{sub}</div>{/if}
</div>

<style>
  .stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.1rem 1.35rem; box-shadow: var(--shadow);
  }
  .label { font-size:.74rem; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; font-weight:600; }
  .value { font-family:var(--font-display); font-size:1.9rem; color:var(--ink); margin-top:.15rem; line-height:1; }
  .sub   { font-size:.78rem; color:var(--muted); margin-top:.25rem; }
</style>
