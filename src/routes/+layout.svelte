<script>
  import { page } from '$app/stores';
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,700;1,400&display=swap" rel="stylesheet">
</svelte:head>

<slot />

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }

  :global(:root) {
    --red:      #d00000;
    --red-dark: #a00000;
    --cream:    #faf8f4;
    --ink:      #1a1a1a;
    --muted:    #6b6b6b;
    --border:   #e4e0d8;
    --surface:  #ffffff;
    --green:    #2d7d46;
    --amber:    #c97b00;
    --blue:     #1d5fa8;

    --font-sans: 'DM Sans', sans-serif;
    --font-mono: 'DM Mono', monospace;
    --font-display: 'Fraunces', serif;

    --radius: 10px;
    --shadow: 0 1px 3px rgba(0,0,0,.07), 0 4px 16px rgba(0,0,0,.06);
    --shadow-lg: 0 8px 32px rgba(0,0,0,.12);
  }

  :global(body) {
    font-family: var(--font-sans);
    background: var(--cream);
    color: var(--ink);
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  :global(h1,h2,h3,h4) { font-family: var(--font-display); line-height: 1.2; }

  :global(a) { color: var(--red); text-decoration: none; }
  :global(a:hover) { text-decoration: underline; }

  :global(.card) {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
  }

  :global(.badge) {
    display: inline-block;
    padding: .2rem .6rem;
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 500;
    font-family: var(--font-mono);
    background: var(--cream);
    border: 1px solid var(--border);
    color: var(--muted);
  }

  :global(.badge.red)   { background: #fde8e8; border-color: #f5b8b8; color: var(--red-dark); }
  :global(.badge.green) { background: #e6f4ec; border-color: #a8d8b8; color: var(--green); }
  :global(.badge.blue)  { background: #e6effa; border-color: #a8c5e8; color: var(--blue); }
  :global(.badge.amber) { background: #fdf3e0; border-color: #f0cf88; color: var(--amber); }

  :global(.stat-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
  }

  :global(.stat-card) {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
  }
  :global(.stat-card .label) { font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; font-weight: 500; }
  :global(.stat-card .value) { font-family: var(--font-display); font-size: 2rem; color: var(--ink); margin-top: .2rem; }
  :global(.stat-card .sub)   { font-size: .8rem; color: var(--muted); margin-top: .1rem; }
</style>
