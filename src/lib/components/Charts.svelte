<script>
  import { onMount } from 'svelte';

  export let visits        = [];
  export let attempts      = [];
  export let locationTypes = {};

  let heatmapEl, treemapEl, scatterEl, moodEl;

  const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const TREE_COLORS = ['#d00000','#1d5fa8','#2d7d46','#c97b00','#9b59b6','#16a085','#e67e22','#555','#3498db'];
  const TYPE_COLOR  = {
    Tutoring:'#d00000', Study:'#1d5fa8', Dining:'#c97b00',
    Testing:'#555', Parking:'#9b59b6', Academic:'#2d7d46',
    Residential:'#e67e22', Recreation:'#16a085', Other:'#aaa',
  };

  onMount(async () => {
    const d3 = await import('https://cdn.jsdelivr.net/npm/d3@7/+esm');
    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);

    // ── Derive all data here so props are live ────────────────

    // Heatmap
    const heatmap = Array.from({length:7}, () => Array(24).fill(0));
    for (const v of visits) {
      const d = new Date(v.date);
      if (isNaN(d)) continue;
      heatmap[d.getDay()][d.getHours()]++;
    }
    const heatMax = Math.max(...heatmap.flat(), 1);

    // Treemap
    const typeVisits = {};
    for (const v of visits) {
      const t = locationTypes[v.location_id] ?? 'Other';
      typeVisits[t] = (typeVisits[t] ?? 0) + 1;
    }
    const treemapData = Object.entries(typeVisits)
      .map(([name, value]) => ({ name, value }))
      .sort((a,b) => b.value - a.value);

    // Scatter: visit duration by location type
    const durationByType = {};
    for (const v of visits) {
      if (!v.duration_minutes) continue;
      const t = locationTypes[v.location_id] ?? 'Other';
      durationByType[t] = durationByType[t] ?? [];
      durationByType[t].push(v.duration_minutes);
    }
    const TYPE_ORDER = Object.keys(durationByType).sort();
    const scatterDatasets = TYPE_ORDER.map((type, idx) => ({
      label: type,
      data: durationByType[type].map(dur => ({
        x: idx + (Math.random() - 0.5) * 0.4,
        y: dur,
      })),
      backgroundColor: (TYPE_COLOR[type] ?? '#aaa') + 'aa',
      pointRadius: 4,
    }));

    // Mood trend
    const moodByMonth = {};
    for (const a of attempts) {
      if (!a.created_at) continue;
      const d = new Date(a.created_at);
      if (isNaN(d)) continue;
      const key = d.toLocaleDateString('en-US', { month:'short', year:'2-digit' });
      moodByMonth[key] = moodByMonth[key] ?? { pre:[], post:[], scores:[] };
      if (a.pre_mood)  moodByMonth[key].pre.push(a.pre_mood);
      if (a.post_mood) moodByMonth[key].post.push(a.post_mood);
      if (a.score)     moodByMonth[key].scores.push(a.score);
    }
    const avg        = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
    const moodLabels = Object.keys(moodByMonth).sort((a, b) => {
        return new Date(`1 ${a}`) - new Date(`1 ${b}`);
    });
    const moodPre    = moodLabels.map(m => +(avg(moodByMonth[m].pre).toFixed(2)));
    const moodPost   = moodLabels.map(m => +(avg(moodByMonth[m].post).toFixed(2)));
    const moodScore  = moodLabels.map(m => +(avg(moodByMonth[m].scores).toFixed(1)));

    // ── Heatmap (D3) ──────────────────────────────────────────
    if (heatmapEl) {
      const W = heatmapEl.clientWidth || 500;
      const ml = 38, mt = 20, mb = 30;
      const cellW = (W - ml) / 24;
      const cellH = 26;
      const H = cellH * 7 + mt + mb;

      const svg = d3.select(heatmapEl)
        .append('svg').attr('width', W).attr('height', H);

      const color = d3.scaleSequential()
        .domain([0, heatMax])
        .interpolator(d3.interpolateRgb('#f0ece4', '#d00000'));

      svg.selectAll('.dl').data(DAYS).enter()
        .append('text')
        .attr('x', ml - 5)
        .attr('y', (_, i) => mt + i*cellH + cellH*0.65)
        .attr('text-anchor','end').attr('font-size',10)
        .attr('fill','#6b6b6b').attr('font-family','sans-serif')
        .text(d => d);

      [0,3,6,9,12,15,18,21].forEach(h => {
        svg.append('text')
          .attr('x', ml + h*cellW + cellW/2).attr('y', H - 8)
          .attr('text-anchor','middle').attr('font-size',9)
          .attr('fill','#6b6b6b').attr('font-family','sans-serif')
          .text(h===0?'12a':h<12?`${h}a`:h===12?'12p':`${h-12}p`);
      });

      for (let day=0; day<7; day++) {
        for (let hr=0; hr<24; hr++) {
          const val = heatmap[day][hr];
          svg.append('rect')
            .attr('x', ml + hr*cellW + 1).attr('y', mt + day*cellH + 1)
            .attr('width', cellW-2).attr('height', cellH-2)
            .attr('rx', 3).attr('fill', color(val))
            .append('title').text(`${DAYS[day]} ${hr}:00 — ${val} visit${val===1?'':'s'}`);
        }
      }

      const defs = svg.append('defs');
      const grad = defs.append('linearGradient').attr('id','hm-grad');
      grad.append('stop').attr('offset','0%').attr('stop-color','#f0ece4');
      grad.append('stop').attr('offset','100%').attr('stop-color','#d00000');
      const lx = W - 122, ly = H - 14;
      svg.append('rect').attr('x',lx).attr('y',ly).attr('width',120).attr('height',8).attr('rx',3).attr('fill','url(#hm-grad)');
      svg.append('text').attr('x',lx).attr('y',ly-3).attr('font-size',8).attr('fill','#aaa').attr('font-family','sans-serif').text('fewer');
      svg.append('text').attr('x',lx+120).attr('y',ly-3).attr('font-size',8).attr('fill','#aaa').attr('text-anchor','end').attr('font-family','sans-serif').text('more');
    }

    // ── Treemap (D3) ──────────────────────────────────────────
    if (treemapEl && treemapData.length) {
      const W = treemapEl.clientWidth || 400;
      const H = 320;
      const root = d3.hierarchy({ children: treemapData }).sum(d => d.value);
      d3.treemap().size([W, H]).padding(3)(root);

      const svg = d3.select(treemapEl).append('svg').attr('width', W).attr('height', H);
      const nodes = svg.selectAll('g').data(root.leaves()).enter().append('g')
        .attr('transform', d => `translate(${d.x0},${d.y0})`);

      nodes.append('rect')
        .attr('width',  d => Math.max(0, d.x1-d.x0))
        .attr('height', d => Math.max(0, d.y1-d.y0))
        .attr('rx', 5)
        .attr('fill', (_, i) => TREE_COLORS[i % TREE_COLORS.length])
        .attr('opacity', 0.88);

      nodes.filter(d => d.x1-d.x0 > 55).append('text')
        .attr('x',7).attr('y',16).attr('font-size',11).attr('font-weight',600)
        .attr('fill','#fff').attr('font-family','sans-serif').text(d => d.data.name);

      nodes.filter(d => d.x1-d.x0 > 55 && d.y1-d.y0 > 30).append('text')
        .attr('x',7).attr('y',30).attr('font-size',10)
        .attr('fill','rgba(255,255,255,.75)').attr('font-family','sans-serif')
        .text(d => `${d.data.value} visits`);

      nodes.append('title').text(d => `${d.data.name}: ${d.data.value} visits`);
    }

    // ── Scatter (Chart.js) ────────────────────────────────────
    if (scatterEl && scatterDatasets.length) {
      new Chart(scatterEl, {
        type: 'scatter',
        data: { datasets: scatterDatasets },
        options: {
          responsive: true,
          plugins: {
            legend: { position:'bottom', labels:{ font:{size:10}, boxWidth:10, padding:8 } },
            tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y} min` } }
          },
          scales: {
            x: {
              min: -0.6, max: TYPE_ORDER.length - 0.4,
              ticks: { stepSize:1, callback: val => Number.isInteger(val) ? (TYPE_ORDER[val] ?? '') : '' },
              title: { display:true, text:'Location Type' },
              grid: { display:false },
            },
            y: {
              title: { display:true, text:'Visit Duration (min)' },
              grid: { color:'#f0ece4' },
            }
          }
        }
      });
    }

    // ── Mood trend (Chart.js) ─────────────────────────────────
    if (moodEl && moodLabels.length) {
      new Chart(moodEl, {
        type: 'line',
        data: {
          labels: moodLabels,
          datasets: [
            { label:'Pre-Exam Mood',  data:moodPre,   borderColor:'#c97b00', borderWidth:2, tension:0.4, pointRadius:4, fill:false, yAxisID:'mood' },
            { label:'Post-Exam Mood', data:moodPost,  borderColor:'#2d7d46', borderWidth:2, tension:0.4, pointRadius:4, fill:false, yAxisID:'mood' },
            { label:'Avg Exam Score', data:moodScore, borderColor:'#d00000', backgroundColor:'rgba(208,0,0,.06)', borderWidth:2, tension:0.4, pointRadius:4, fill:true, yAxisID:'score', borderDash:[5,3] },
          ]
        },
        options: {
          responsive: true,
          interaction: { mode:'index', intersect:false },
          plugins: { legend:{ position:'bottom', labels:{ font:{size:11}, boxWidth:12, padding:10 } } },
          scales: {
            mood:  { type:'linear', position:'left',  min:1, max:5,   title:{ display:true, text:'Mood (1–5)' },    grid:{ color:'#f0ece4' } },
            score: { type:'linear', position:'right', min:0, max:100, title:{ display:true, text:'Exam Score' },    grid:{ display:false } },
            x: { grid:{ display:false } }
          }
        }
      });
    }
  });
</script>

<div class="charts">
  <div class="chart-block wide">
    <div class="chart-label">Campus Traffic Heatmap — Visits by Day & Hour</div>
    <div bind:this={heatmapEl} class="d3-area"></div>
    <p class="note">Darker red = more visits. Hover any cell for exact count.</p>
  </div>

  <div class="chart-block">
    <div class="chart-label">Location Type Breakdown</div>
    <div bind:this={treemapEl} class="d3-area"></div>
    <p class="note">Block size = share of total campus visits.</p>
  </div>

  <div class="chart-block">
    <div class="chart-label">Visit Duration by Location Type</div>
    <canvas bind:this={scatterEl}></canvas>
    <p class="note">Each dot is one visit. Shows how long students stay at each location type.</p>
  </div>

  <div class="chart-block wide">
    <div class="chart-label">Mood & Score Trends Over Time</div>
    <canvas bind:this={moodEl}></canvas>
    <p class="note">Pre/post exam mood (left) vs avg exam score (right, dashed).</p>
  </div>
</div>

<style>
  .charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  .chart-block {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.35rem 1.5rem;
    box-shadow: var(--shadow);
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: .6rem;
  }
  .chart-block.wide { grid-column: span 2; }
  .chart-label {
    font-size: .72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em; color: var(--muted);
  }
  .d3-area { width: 100%; overflow: hidden; }
  .note { font-size: .75rem; color: var(--muted); font-style: italic; margin: 0; }

  @media (max-width: 800px) {
    .charts { grid-template-columns: 1fr; }
    .chart-block.wide { grid-column: span 1; }
  }
</style>
