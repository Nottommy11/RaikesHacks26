<script>
  import { onMount }   from 'svelte';
  import PageShell     from '$lib/components/PageShell.svelte';
  import StatCard      from '$lib/components/StatCard.svelte';
  import ChartCard     from '$lib/components/ChartCard.svelte';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  import Charts        from '$lib/components/Charts.svelte';

  export let data;
  const { locations, tagTrends, studyModes, activities,
          tutoringAvg, nonTutoringAvg, lift,
          totalUsers, totalVisits, avgRating, totalReviews,
          visitsForCharts, locationTypes, attemptsForCharts } = data;

  const TYPE_COLOR = {
    Tutoring: '#d00000', Study: '#1d5fa8', Dining: '#c97b00',
    'Dining/General': '#e8a000', Testing: '#555555', Parking: '#9b59b6',
    Academic: '#2d7d46', Residential: '#e67e22', Recreation: '#16a085',
  };
  const PALETTE = [
    '#d00000','#1d5fa8','#2d7d46','#c97b00','#9b59b6','#16a085',
    '#e67e22','#555555','#e74c3c','#3498db','#27ae60','#f39c12',
  ];
  const typeColor = t => TYPE_COLOR[t] ?? '#aaaaaa';
  const maxVisits = Math.max(...locations.map(l => l.visitCount), 1);

  const adminProfile = { username: 'Admin', admin_type: 'Staff' };

  let selectedTag = null;
  function selectTag(t) {
    selectedTag = selectedTag?.tag === t.tag ? null : t;
  }

  let liftCanvas, modeCanvas, hotspotCanvas;

  onMount(async () => {
    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);

    if (liftCanvas) {
      new Chart(liftCanvas, {
        type: 'bar',
        data: {
          labels: ['Used Tutoring Mode', 'Other Study Modes'],
          datasets: [{ data: [parseFloat(tutoringAvg), parseFloat(nonTutoringAvg)],
            backgroundColor: ['#d00000', '#e4e0d8'], borderRadius: 8 }]
        },
        options: { indexAxis: 'y', responsive: true,
          plugins: { legend: { display: false } },
          scales: { x: { min: 0, max: 100 }, y: { grid: { display: false } } } }
      });
    }

    if (modeCanvas) {
      new Chart(modeCanvas, {
        type: 'bar',
        data: {
          labels: studyModes.map(m => m.label),
          datasets: [{ data: studyModes.map(m => parseFloat(m.avg) || 0),
            backgroundColor: ['#1a1a1a','#d00000','#2d7d46','#1d5fa8'],
            borderRadius: 6, barThickness: 36 }]
        },
        options: { responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => ` ${ctx.raw} avg (${studyModes[ctx.dataIndex].count} attempts)` } }
          },
          scales: { y: { min: 0, max: 100 }, x: { grid: { display: false } } } }
      });
    }

    if (hotspotCanvas) {
      const top = locations.slice(0, 12);
      new Chart(hotspotCanvas, {
        type: 'doughnut',
        data: {
          labels: top.map(l => l.name),
          datasets: [{ data: top.map(l => l.visitCount),
            backgroundColor: top.map((_, i) => PALETTE[i % PALETTE.length]),
            borderWidth: 2, borderColor: '#faf8f4' }]
        },
        options: { responsive: true, cutout: '55%',
          plugins: { legend: { position: 'bottom',
            labels: { font: { size: 10 }, boxWidth: 10, padding: 8 } } } }
      });
    }
  });
</script>

<PageShell profile={adminProfile} role="admin" active="overview">

  <div>
    <h1 style="font-size:1.9rem">Campus Analytics</h1>
    <p style="color:var(--muted);margin-top:.3rem">Aggregated, anonymized insights across all students.</p>
  </div>

  <div class="stat-grid">
    <StatCard label="Total Students" value={totalUsers}  sub="in the system" />
    <StatCard label="Campus Visits"  value={totalVisits} sub="logged total" />
    <StatCard label="Avg Rating"     value={avgRating}   sub="across {totalReviews} reviews" />
    <StatCard label="Tutoring Lift"  value={lift}        sub="avg score points" color="green" />
  </div>

  <!-- Deep dive charts -->
  <section>
    <SectionHeader title="Data Insights"
      sub="Patterns across visits, study habits, and student wellbeing." />
    <Charts
      visits={visitsForCharts}
      attempts={attemptsForCharts}
      locationTypes={locationTypes}
    />
  </section>

  <!-- Hotspots + Study modes -->
  <section id="hotspots">
    <SectionHeader title="Campus Hotspots" />
    <div class="chart-grid">
      <ChartCard label="Visit Distribution">
        <canvas bind:this={hotspotCanvas}></canvas>
      </ChartCard>
      <ChartCard label="Avg Score by Study Mode">
        <canvas bind:this={modeCanvas}></canvas>
        <div class="mode-list">
          {#each studyModes as m}
            <div class="mode-row">
              <span class="mode-label">{m.label}</span>
              <span class="badge {parseFloat(m.avg)>=80?'green':parseFloat(m.avg)>=70?'blue':'amber'}">{m.avg}</span>
              <span class="muted">{m.count} attempts</span>
            </div>
          {/each}
        </div>
      </ChartCard>
    </div>

    <div class="card">
      <div class="card-label">All Locations</div>
      <div class="loc-list">
        {#each locations as l}
          <div class="loc-row">
            <div class="loc-info">
              <span class="loc-dot" style="background:{typeColor(l.type)}"></span>
              <div class="loc-text">
                <strong>{l.name}</strong>
                <small>{l.type}</small>
              </div>
            </div>
            <div class="loc-bar-wrap">
              <div class="loc-bar" style="width:{Math.round(l.visitCount/maxVisits*100)}%;background:{typeColor(l.type)}99"></div>
              <span class="muted">{l.visitCount} visits</span>
            </div>
            <div class="loc-rating">
              {#if l.avgRating}
                ⭐ {l.avgRating} <small>{l.reviewCount} reviews</small>
              {:else}
                <small class="muted">no reviews</small>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Tutoring lift -->
  <section id="tutoring">
    <SectionHeader title="Tutoring Impact" />
    <div class="card">
      <div class="card-label">Avg Score: Tutoring Mode vs Other Study Modes</div>
      <canvas bind:this={liftCanvas} style="max-height:120px"></canvas>
      <div class="callout">
        Students who used tutoring mode averaged <strong>{tutoringAvg}</strong> vs
        <strong>{nonTutoringAvg}</strong> for other modes —
        a <strong style="color:var(--green)">{lift} point</strong> difference.
      </div>
    </div>
  </section>

  <!-- Tag trends -->
  <section id="tags">
    <SectionHeader title="Interest Trends" sub="Click any tag to see related courses and clubs." />
    <div class="card">
      <div class="tag-cloud">
        {#each tagTrends as t}
          {@const size = 0.82 + (t.count / tagTrends[0].count) * 0.9}
          <button
            class="tag-chip"
            class:selected={selectedTag?.tag === t.tag}
            style="font-size:{size}rem"
            on:click={() => selectTag(t)}
          >
            {t.tag}<sup>{t.count}</sup>
          </button>
        {/each}
      </div>
    </div>

    {#if selectedTag}
      <div class="card drill-down">
        <div class="drill-header">
          <div>
            <strong>{selectedTag.tag}</strong>
            <span class="muted">— {selectedTag.count} students interested</span>
          </div>
          <button class="close-btn" on:click={() => selectedTag = null}>×</button>
        </div>
        <div class="drill-grid">
          <div>
            <div class="drill-label">Courses</div>
            {#if selectedTag.courses.length}
              <div class="drill-list">
                {#each selectedTag.courses as c}
                  <div class="drill-item">
                    <span class="badge blue">{c.course_id}</span>
                    <span>{c.name}</span>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="muted">No tagged courses found.</p>
            {/if}
          </div>
          <div>
            <div class="drill-label">Clubs & Activities</div>
            {#if selectedTag.activities.length}
              <div class="drill-list">
                {#each selectedTag.activities as a}
                  <div class="drill-item">
                    <span class="badge {a.type==='tutoring'?'red':'green'}">{a.type}</span>
                    <span>{a.name}</span>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="muted">No tagged activities found.</p>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </section>

  <!-- Top activities -->
  <section id="activities">
    <SectionHeader title="Most Visited Activities" />
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Activity</th><th>Type</th><th>Location</th><th>Visits</th><th>Avg Duration</th></tr>
          </thead>
          <tbody>
            {#each activities as a}
              <tr>
                <td><strong>{a.name}</strong></td>
                <td><span class="badge {a.type==='tutoring'?'red':'blue'}">{a.type}</span></td>
                <td>{a.location?.name ?? '—'}</td>
                <td>{a.visitCount}</td>
                <td>{a.avgDuration} min</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </section>

</PageShell>

<style>
  .stat-grid  { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.85rem; }
  .chart-grid { display:grid; grid-template-columns:1fr 1fr; gap:.85rem; }
  section     { display:flex; flex-direction:column; gap:.85rem; }

  .card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); padding:1.25rem 1.5rem; box-shadow:var(--shadow);
  }
  .card-label {
    font-size:.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted); margin-bottom:.85rem;
  }
  .callout {
    margin-top:1rem; padding:.8rem 1rem; background:#e6f4ec;
    border-radius:8px; font-size:.875rem; color:#1a4a28; border:1px solid #a8d8b8;
  }

  .mode-list  { display:flex; flex-direction:column; gap:.5rem; margin-top:1rem; }
  .mode-row   { display:flex; align-items:center; gap:.75rem; font-size:.875rem; }
  .mode-label { width:70px; flex-shrink:0; }

  .loc-list { display:flex; flex-direction:column; }
  .loc-row  {
    display:grid; grid-template-columns:minmax(0,2fr) minmax(0,2fr) 110px;
    align-items:center; gap:.75rem;
    padding:.5rem 0; border-bottom:1px solid var(--border); font-size:.82rem;
  }
  .loc-row:last-child { border-bottom:none; }
  .loc-info  { display:flex; align-items:center; gap:.5rem; min-width:0; }
  .loc-dot   { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
  .loc-text  { min-width:0; }
  .loc-text strong { display:block; font-size:.82rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .loc-text small  { color:var(--muted); font-size:.72rem; }
  .loc-bar-wrap { display:flex; align-items:center; gap:.5rem; }
  .loc-bar  { height:7px; border-radius:4px; min-width:2px; }
  .loc-rating { text-align:right; font-size:.8rem; white-space:nowrap; }
  .loc-rating small { display:block; color:var(--muted); font-size:.7rem; }

  .tag-cloud { display:flex; flex-wrap:wrap; gap:.6rem; align-items:baseline; }
  .tag-chip {
    font-family:var(--font-mono); background:var(--cream);
    border:1px solid var(--border); border-radius:999px;
    padding:.22rem .65rem; cursor:pointer; transition:all .15s; line-height:1.4;
  }
  .tag-chip:hover    { background:#fde8e8; border-color:#f5b8b8; }
  .tag-chip.selected { background:var(--red); border-color:var(--red); color:#fff; }
  .tag-chip.selected sup { color:rgba(255,255,255,.6); }
  .tag-chip sup { color:var(--muted); font-size:.6em; margin-left:.15rem; }

  .drill-down   { border-color:var(--red); border-width:1.5px; }
  .drill-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.1rem; }
  .drill-header strong { font-size:1rem; }
  .close-btn {
    background:none; border:none; cursor:pointer;
    font-size:1.4rem; color:var(--muted); line-height:1;
    padding:.1rem .4rem; border-radius:4px; transition:color .15s;
  }
  .close-btn:hover { color:var(--ink); }
  .drill-grid  { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }
  .drill-label { font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin-bottom:.6rem; }
  .drill-list  { display:flex; flex-direction:column; gap:.45rem; }
  .drill-item  { display:flex; align-items:center; gap:.5rem; font-size:.85rem; }

  .table-wrap { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; font-size:.875rem; }
  th {
    text-align:left; font-size:.72rem; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted);
    padding:.5rem .75rem; border-bottom:1px solid var(--border); font-weight:600;
  }
  td { padding:.6rem .75rem; border-bottom:1px solid var(--border); }
  tr:last-child td { border-bottom:none; }
  tr:hover td { background:var(--cream); }

  .muted { color:var(--muted); font-size:.82rem; }

  @media (max-width:700px) {
    .chart-grid { grid-template-columns:1fr; }
    .drill-grid { grid-template-columns:1fr; }
    .loc-row    { grid-template-columns:1fr 1fr; }
  }
</style>
