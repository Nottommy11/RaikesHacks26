<script>
  import PageShell     from '$lib/components/PageShell.svelte';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  export let data;

  let { uid, profile, myTags, allTags, suggestions } = data;

  let currentTags   = [...myTags];
  let search        = '';
  let searchResults = [];
  let youtubeUrl    = '';
  let articleUrl    = '';
  let ytLoading     = false;
  let artLoading    = false;
  let ytResult      = null;
  let artResult     = null;
  let ytError       = '';
  let artError      = '';
  let toast         = '';
  let toastTimer;

  const tagIds = () => new Set(currentTags.map(t => t.tag_id));

  $: {
    if (search.length >= 3) {
      const q = search.toLowerCase();
      searchResults = allTags.filter(t => t.includes(q) && !tagIds().has(t)).slice(0, 20);
    } else {
      searchResults = [];
    }
  }

  function showToast(msg) {
    toast = msg;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast = '', 2500);
  }

  async function addTag(tag_id) {
    if (tagIds().has(tag_id)) return;
    const res = await fetch('/api/interests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: uid, tag_id }),
    });
    if (res.ok) {
      currentTags  = [...currentTags, { interest_id: crypto.randomUUID(), tag_id }];
      suggestions  = suggestions.filter(s => s !== tag_id);
      search = '';
      showToast(`Added "${tag_id}"`);
    }
  }

  async function removeTag(tag_id) {
    const res = await fetch('/api/interests', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: uid, tag_id }),
    });
    if (res.ok) {
      currentTags = currentTags.filter(t => t.tag_id !== tag_id);
      showToast(`Removed "${tag_id}"`);
    }
  }

  async function fetchYouTube() {
    if (!youtubeUrl.trim()) return;
    ytLoading = true; ytResult = null; ytError = '';
    try {
      const res  = await fetch(`/api/youtube?url=${encodeURIComponent(youtubeUrl)}`);
      const json = await res.json();
      if (json.error) { ytError = json.error; return; }
      const allTagSet = new Set(allTags);
      const matched = [], proposed = [], seen = new Set();
      for (const c of [...json.rawTags, ...json.titleWords, ...json.descWords]) {
        if (seen.has(c) || tagIds().has(c)) continue;
        seen.add(c);
        if (allTagSet.has(c)) matched.push(c);
        else proposed.push(c);
        if (matched.length + proposed.length >= 10) break;
      }
      ytResult = { ...json, matched, proposed };
    } catch { ytError = 'Request failed.'; }
    finally  { ytLoading = false; }
  }

  async function fetchArticle() {
    if (!articleUrl.trim()) return;
    artLoading = true; artResult = null; artError = '';
    try {
      const res  = await fetch(`/api/scrape?url=${encodeURIComponent(articleUrl)}`);
      const json = await res.json();
      if (json.error) { artError = json.error; return; }
      const allTagSet = new Set(allTags);
      const matched = [], proposed = [], seen = new Set();
      for (const c of [...json.keywords, ...json.categories, ...json.textWords]) {
        const clean = c.toLowerCase().trim();
        if (!clean || seen.has(clean) || tagIds().has(clean)) continue;
        seen.add(clean);
        if (allTagSet.has(clean)) matched.push(clean);
        else proposed.push(clean);
        if (matched.length + proposed.length >= 10) break;
      }
      artResult = { title: json.title, matched, proposed };
    } catch { artError = 'Request failed.'; }
    finally  { artLoading = false; }
  }
</script>

<PageShell {profile} role="student" {uid} active="interests">

  <div class="page-header">
    <div>
      <h1>My Interests</h1>
      <p class="muted">Tags shape your course suggestions, club recommendations, and resource matches.</p>
    </div>
    <span class="count-badge">{currentTags.length} tags</span>
  </div>

  <!-- Current tags -->
  <section>
    <SectionHeader title="Your Tags" />
    {#if currentTags.length === 0}
      <div class="empty-state">No tags yet — add some below.</div>
    {:else}
      <div class="tag-cloud">
        {#each currentTags as t (t.tag_id)}
          <span class="chip current">
            {t.tag_id}
            <button class="x" on:click={() => removeTag(t.tag_id)}>×</button>
          </span>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Suggestions -->
  {#if suggestions.filter(s => !tagIds().has(s)).length > 0}
    <section>
      <SectionHeader title="Suggested for You" sub="Based on your enrolled courses and similar students." />
      <div class="tag-cloud">
        {#each suggestions.filter(s => !tagIds().has(s)) as s}
          <button class="chip suggest" on:click={() => addTag(s)}>+ {s}</button>
        {/each}
      </div>
    </section>
  {/if}

  <!-- Search -->
  <section>
    <SectionHeader title="Search & Add" sub="Results appear after 3 characters." />
    <div class="search-wrap">
      <input class="input" type="text" bind:value={search}
        placeholder="e.g. machine learning, robotics..." />
      {#if search.length > 0 && search.length < 3}
        <p class="hint">Keep typing…</p>
      {/if}
      {#if searchResults.length > 0}
        <div class="dropdown">
          {#each searchResults as r}
            <button class="dropdown-row" on:click={() => addTag(r)}>
              <span>{r}</span><span class="add-label">Add +</span>
            </button>
          {/each}
        </div>
      {:else if search.length >= 3}
        <p class="hint">No matches found.</p>
      {/if}
    </div>
  </section>

  <!-- YouTube -->
  <section>
    <SectionHeader title="Add from YouTube" sub="Paste a video URL — we extract tags from title, description, and metadata." />
    <div class="url-row">
      <input class="input" type="text" bind:value={youtubeUrl}
        placeholder="https://youtube.com/watch?v=..."
        on:keydown={e => e.key==='Enter' && fetchYouTube()} />
      <button class="btn" on:click={fetchYouTube} disabled={ytLoading || !youtubeUrl.trim()}>
        {ytLoading ? 'Fetching…' : 'Extract Tags'}
      </button>
    </div>
    {#if ytError}<div class="error">{ytError}</div>{/if}
    {#if ytResult}
      <div class="card">
        <div class="media-header">
          {#if ytResult.thumbnail}<img src={ytResult.thumbnail} alt="" class="thumb" />{/if}
          <div><strong>{ytResult.title}</strong><small class="muted">{ytResult.channel}</small></div>
        </div>
        {#if ytResult.matched.length}
          <div class="tag-group">
            <div class="group-label">Matches your tag library</div>
            <div class="tag-cloud">
              {#each ytResult.matched as t}
                <button class="chip suggest {tagIds().has(t)?'added':''}"
                  on:click={() => addTag(t)} disabled={tagIds().has(t)}>
                  {tagIds().has(t) ? '✓ ' : '+ '}{t}
                </button>
              {/each}
            </div>
          </div>
        {/if}
        {#if ytResult.proposed.length}
          <div class="tag-group">
            <div class="group-label">Not in library yet</div>
            <div class="tag-cloud">
              {#each ytResult.proposed as t}<span class="chip muted">{t}</span>{/each}
            </div>
            <p class="hint">Ask an admin to add relevant ones.</p>
          </div>
        {/if}
      </div>
    {/if}
  </section>

  <!-- Article -->
  <section>
    <SectionHeader title="Add from an Article" sub="Paste any article or blog URL — we extract topic keywords from the page." />
    <div class="url-row">
      <input class="input" type="text" bind:value={articleUrl}
        placeholder="https://..."
        on:keydown={e => e.key==='Enter' && fetchArticle()} />
      <button class="btn" on:click={fetchArticle} disabled={artLoading || !articleUrl.trim()}>
        {artLoading ? 'Fetching…' : 'Extract Tags'}
      </button>
    </div>
    {#if artError}<div class="error">{artError}</div>{/if}
    {#if artResult}
      <div class="card">
        <div class="media-header">
          <div><strong>{artResult.title || articleUrl}</strong><small class="muted">Article</small></div>
        </div>
        {#if artResult.matched.length}
          <div class="tag-group">
            <div class="group-label">Matches your tag library</div>
            <div class="tag-cloud">
              {#each artResult.matched as t}
                <button class="chip suggest {tagIds().has(t)?'added':''}"
                  on:click={() => addTag(t)} disabled={tagIds().has(t)}>
                  {tagIds().has(t) ? '✓ ' : '+ '}{t}
                </button>
              {/each}
            </div>
          </div>
        {/if}
        {#if artResult.proposed.length}
          <div class="tag-group">
            <div class="group-label">Not in library yet</div>
            <div class="tag-cloud">
              {#each artResult.proposed as t}<span class="chip muted">{t}</span>{/each}
            </div>
            <p class="hint">Ask an admin to add relevant ones.</p>
          </div>
        {/if}
        {#if !artResult.matched.length && !artResult.proposed.length}
          <p class="hint">Couldn't extract useful tags — this page may block scrapers or have limited metadata.</p>
        {/if}
      </div>
    {/if}
  </section>

</PageShell>

{#if toast}
  <div class="toast">{toast}</div>
{/if}

<style>
  .page-header { display:flex; justify-content:space-between; align-items:flex-start; }
  .page-header h1 { font-size:1.9rem; }
  .page-header .muted { color:var(--muted); margin-top:.3rem; font-size:.9rem; }
  .count-badge {
    font-family:var(--font-mono); font-size:.82rem;
    background:var(--surface); border:1px solid var(--border);
    padding:.4rem .9rem; border-radius:999px; color:var(--muted); white-space:nowrap;
  }

  section { display:flex; flex-direction:column; gap:.85rem; }

  .empty-state {
    color:var(--muted); font-size:.9rem; padding:1.5rem;
    background:var(--surface); border:1px dashed var(--border);
    border-radius:var(--radius); text-align:center;
  }

  .tag-cloud { display:flex; flex-wrap:wrap; gap:.5rem; }

  .chip {
    display:inline-flex; align-items:center; gap:.3rem;
    padding:.28rem .7rem; border-radius:999px; font-size:.8rem;
    font-family:var(--font-mono); border:1px solid var(--border);
    background:var(--surface); color:var(--ink);
  }
  .chip.current { background:#fde8e8; border-color:#f5b8b8; color:var(--red-dark); }
  .chip.suggest {
    background:#e6effa; border-color:#a8c5e8; color:var(--blue);
    cursor:pointer; transition:all .15s;
  }
  .chip.suggest:hover:not(:disabled) { background:var(--blue); color:#fff; border-color:var(--blue); }
  .chip.suggest.added { background:#e6f4ec; border-color:#a8d8b8; color:var(--green); cursor:default; }
  .chip.muted { background:var(--cream); color:var(--muted); border-style:dashed; }

  .x {
    background:none; border:none; cursor:pointer;
    font-size:1rem; line-height:1; color:var(--red-dark);
    opacity:.6; padding:0; transition:opacity .1s;
  }
  .x:hover { opacity:1; }

  .search-wrap { position:relative; max-width:480px; }
  .input {
    width:100%; padding:.7rem 1rem;
    border:1.5px solid var(--border); border-radius:8px;
    font-family:var(--font-sans); font-size:.92rem;
    background:var(--surface); color:var(--ink);
    outline:none; transition:border-color .15s;
  }
  .input:focus { border-color:var(--red); }
  .hint { font-size:.8rem; color:var(--muted); margin-top:.35rem; }

  .dropdown {
    position:absolute; top:calc(100% + 4px); left:0; right:0;
    background:var(--surface); border:1px solid var(--border);
    border-radius:8px; box-shadow:var(--shadow-lg);
    z-index:100; overflow:hidden; max-height:260px; overflow-y:auto;
  }
  .dropdown-row {
    display:flex; justify-content:space-between; align-items:center;
    width:100%; padding:.6rem 1rem; background:none; border:none;
    border-bottom:1px solid var(--border); cursor:pointer;
    font-family:var(--font-mono); font-size:.83rem; color:var(--ink);
    text-align:left; transition:background .1s;
  }
  .dropdown-row:last-child { border-bottom:none; }
  .dropdown-row:hover { background:var(--cream); }
  .add-label { font-size:.73rem; color:var(--blue); font-weight:600; }

  .url-row { display:flex; gap:.75rem; max-width:600px; }
  .btn {
    padding:.7rem 1.2rem; background:var(--red); color:#fff;
    border:none; border-radius:8px; font-family:var(--font-sans);
    font-size:.88rem; font-weight:600; cursor:pointer; white-space:nowrap; transition:background .15s;
  }
  .btn:hover:not(:disabled) { background:var(--red-dark); }
  .btn:disabled { opacity:.45; cursor:not-allowed; }

  .error {
    color:var(--red); font-size:.85rem; padding:.6rem 1rem;
    background:#fde8e8; border-radius:8px; border:1px solid #f5b8b8;
  }

  .card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); padding:1.25rem 1.4rem;
    display:flex; flex-direction:column; gap:1.1rem; box-shadow:var(--shadow);
  }
  .media-header { display:flex; gap:1rem; align-items:center; }
  .thumb { width:110px; border-radius:6px; flex-shrink:0; object-fit:cover; }
  .media-header strong { display:block; font-size:.92rem; margin-bottom:.2rem; }

  .tag-group { display:flex; flex-direction:column; gap:.4rem; }
  .group-label { font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); }

  .muted { color:var(--muted); font-size:.82rem; }

  .toast {
    position:fixed; bottom:2rem; left:50%; transform:translateX(-50%);
    background:var(--ink); color:#fff; padding:.65rem 1.5rem;
    border-radius:999px; font-size:.88rem; font-weight:500;
    box-shadow:var(--shadow-lg); z-index:999; pointer-events:none;
    animation:fadeup .2s ease;
  }
  @keyframes fadeup {
    from { opacity:0; transform:translateX(-50%) translateY(8px); }
    to   { opacity:1; transform:translateX(-50%) translateY(0); }
  }
</style>
