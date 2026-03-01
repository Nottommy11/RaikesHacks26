<script>
  import { onMount }   from 'svelte';
  import PageShell     from '$lib/components/PageShell.svelte';
  import StatCard      from '$lib/components/StatCard.svelte';
  import ChartCard     from '$lib/components/ChartCard.svelte';
  import SectionHeader from '$lib/components/SectionHeader.svelte';

  export let data;
  const {
    uid, profile, enrollment, attempts, visits,
    tutoring, suggestedClubs, avgScore, modeCount, visitsByType,
    allTerms, latestTerm, recommendedCourses,
    locationsWithReviews, activitiesWithReviews,
    visitedLocationIds, visitedActivityIds,
    allCourses,
  } = data;

  const MOOD = ['','😟','😕','😐','🙂','😄'];
  const scoreColor = s => s >= 90 ? 'green' : s >= 75 ? 'blue' : s >= 60 ? 'amber' : 'red';

  // ── Term selector ─────────────────────────────────────────────
  let selectedTerm = latestTerm;
  $: filteredCourses = enrollment.filter(e => !selectedTerm || e.term === selectedTerm);

  // ── Course search ─────────────────────────────────────────────
  let courseSearch  = '';
  let courseResults = [];
  $: {
    if (courseSearch.length >= 3) {
      const q = courseSearch.toLowerCase();
      courseResults = allCourses
        .filter(c =>
          c.course_id.toLowerCase().includes(q) ||
          c.name.toLowerCase().includes(q) ||
          c.tags.some(t => t.toLowerCase().includes(q))
        )
        .slice(0, 15);
    } else {
      courseResults = [];
    }
  }

  // ── Review form ───────────────────────────────────────────────
  let reviewTarget  = 'location';
  let reviewLocId   = '';
  let reviewActId   = '';
  let reviewRating  = 0;
  let reviewText    = '';
  let reviewLoading = false;
  let reviewToast   = '';
  let reviewTimer;
  let myReviews     = [];

  const visitedLocs = new Set(visitedLocationIds);
  const visitedActs = new Set(visitedActivityIds);

  const sortedLocations = [...locationsWithReviews].sort((a,b) => {
    return (visitedLocs.has(a.location_id)?0:1) - (visitedLocs.has(b.location_id)?0:1)
      || a.name.localeCompare(b.name);
  });
  const sortedActivities = [...activitiesWithReviews].sort((a,b) => {
    return (visitedActs.has(a.activity_id)?0:1) - (visitedActs.has(b.activity_id)?0:1)
      || a.name.localeCompare(b.name);
  });

  const locNameMap = Object.fromEntries(locationsWithReviews.map(l => [l.location_id, l.name]));
  const actNameMap = Object.fromEntries(activitiesWithReviews.map(a => [a.activity_id, a.name]));

  function showReviewToast(msg) {
    reviewToast = msg;
    clearTimeout(reviewTimer);
    reviewTimer = setTimeout(() => reviewToast = '', 3000);
  }

  async function submitReview() {
    if (!reviewRating) return;
    if (reviewTarget === 'location' && !reviewLocId) return;
    if (reviewTarget === 'activity' && !reviewActId) return;
    reviewLoading = true;
    try {
      const res = await fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id:     uid,
          location_id: reviewTarget === 'location' ? reviewLocId : null,
          activity_id: reviewTarget === 'activity' ? reviewActId : null,
          rating:      reviewRating,
          review_text: reviewText || null,
        }),
      });
      if (res.ok) {
        showReviewToast('Review submitted — thanks!');
        myReviews = [...myReviews, {
          target_name: reviewTarget === 'location'
            ? locNameMap[reviewLocId]
            : actNameMap[reviewActId],
          target_type: reviewTarget,
          rating:      reviewRating,
          review_text: reviewText || null,
        }];
        reviewRating = 0;
        reviewText   = '';
        reviewLocId  = '';
        reviewActId  = '';
      } else {
        const err = await res.json().catch(() => ({}));
        showReviewToast(`Error: ${err.error ?? 'Submission failed'}`);
      }
    } catch (e) {
      showReviewToast('Network error — try again');
    } finally {
      reviewLoading = false;
    }
  }

  // ── Charts ────────────────────────────────────────────────────
  let modeCanvas, moodCanvas, studyScoreCanvas;

  onMount(async () => {
    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);

    // Mood + score over time
    if (moodCanvas && attempts.length) {
      const sorted = [...attempts].sort((a,b) => new Date(a.created_at) - new Date(b.created_at));
      new Chart(moodCanvas, {
        type: 'line',
        data: {
          labels: sorted.map(a => a.exam?.name ?? a.exam?.course_id ?? '—'),
          datasets: [
            {
              label: 'Pre-Exam Mood',
              data: sorted.map(a => a.pre_mood),
              borderColor: '#c97b00', borderWidth: 2, tension: 0.4,
              pointRadius: 5, fill: false, yAxisID: 'mood',
            },
            {
              label: 'Post-Exam Mood',
              data: sorted.map(a => a.post_mood),
              borderColor: '#2d7d46', borderWidth: 2, tension: 0.4,
              pointRadius: 5, fill: false, yAxisID: 'mood',
            },
            {
              label: 'Score',
              data: sorted.map(a => a.score),
              borderColor: '#d00000', backgroundColor: 'rgba(208,0,0,.07)',
              borderWidth: 2, tension: 0.3, pointRadius: 5,
              fill: true, yAxisID: 'score', borderDash: [5,3],
            },
          ]
        },
        options: {
          responsive: true,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'bottom', labels: { font: { size: 11 }, boxWidth: 12 } },
            tooltip: {
              callbacks: {
                afterBody: (items) => {
                  const idx = items[0]?.dataIndex;
                  if (idx == null) return '';
                  return `Study mode: ${sorted[idx].study_mode}`;
                }
              }
            }
          },
          scales: {
            mood:  { type:'linear', position:'left',  min:1, max:5,   title:{ display:true, text:'Mood (1–5)' }, grid:{ color:'#f0ece4' } },
            score: { type:'linear', position:'right', min:0, max:100, title:{ display:true, text:'Score' },      grid:{ display:false } },
            x: { grid:{ display:false }, ticks:{ maxRotation:35, font:{ size:10 } } }
          }
        }
      });
    }

    // Study mode doughnut
    if (modeCanvas && Object.keys(modeCount).length) {
      new Chart(modeCanvas, {
        type: 'doughnut',
        data: {
          labels: Object.keys(modeCount),
          datasets: [{ data: Object.values(modeCount),
            backgroundColor: ['#d00000','#1d5fa8','#2d7d46','#c97b00'], borderWidth: 0 }]
        },
        options: { responsive: true, cutout: '65%',
          plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } } }
      });
    }

    // Avg score by study mode
    if (studyScoreCanvas && attempts.length) {
      const modeScores = {};
      for (const a of attempts) {
        modeScores[a.study_mode] = modeScores[a.study_mode] ?? [];
        modeScores[a.study_mode].push(a.score);
      }
      const avg = arr => arr.length ? Math.round(arr.reduce((a,b)=>a+b,0)/arr.length) : 0;
      const labels = Object.keys(modeScores);
      new Chart(studyScoreCanvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            data: labels.map(m => avg(modeScores[m])),
            backgroundColor: ['#d00000','#1d5fa8','#2d7d46','#c97b00'],
            borderRadius: 6, barThickness: 36,
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: {
              label: ctx => ` Avg: ${ctx.raw} (${modeScores[labels[ctx.dataIndex]].length} attempts)`
            }}
          },
          scales: {
            y: { min:0, max:100, grid:{ color:'#f0ece4' } },
            x: { grid:{ display:false } }
          }
        }
      });
    }
  });
</script>

<PageShell {profile} role="student" {uid} active="dashboard">

  <div>
    <h1 style="font-size:1.9rem">Good to see you, {profile.first_name}.</h1>
    <p style="color:var(--muted);margin-top:.3rem">Here's how things look across your courses and campus activity.</p>
  </div>

  <div class="stat-grid">
    <StatCard label="Avg Exam Score"   value={avgScore ?? '—'} sub="{attempts.length} attempts"
      color={avgScore >= 75 ? 'green' : avgScore >= 60 ? 'amber' : 'red'} />
    <StatCard label="Courses Enrolled" value={enrollment.length} sub="total" />
    <StatCard label="Campus Visits"    value={visits.length}     sub="logged" />
    <StatCard label="Interests Tagged" value={data.interests.length} sub="topics" />
  </div>

  <section>
    <SectionHeader title="Exam Performance" />
    <div class="chart-grid-3">
      <ChartCard label="Mood & Score Over Time" wide2>
        {#if attempts.length}
          <canvas bind:this={moodCanvas}></canvas>
          <p class="chart-note">Hover any point to see study mode used.</p>
        {:else}
          <p class="empty">No attempts yet.</p>
        {/if}
      </ChartCard>
      <ChartCard label="Study Modes Used">
        {#if Object.keys(modeCount).length}
          <canvas bind:this={modeCanvas}></canvas>
        {:else}<p class="empty">No data.</p>{/if}
      </ChartCard>
    </div>
  </section>

  <section>
    <SectionHeader title="Enrolled Courses" />
    <div class="courses-layout">
      <div class="term-sidebar">
        <div class="term-label">Filter by term</div>
        <button class="term-btn" class:active={selectedTerm === null}
          on:click={() => selectedTerm = null}>All</button>
        {#each allTerms as term}
          <button class="term-btn" class:active={selectedTerm === term}
            on:click={() => selectedTerm = term}>{term}</button>
        {/each}
      </div>
      <div class="pill-grid">
        {#each filteredCourses as e}
          <div class="card course-card">
            <span class="badge blue">{e.course_id}</span>
            <small class="muted">{e.term}</small>
          </div>
        {:else}
          <p class="empty">No courses for this term.</p>
        {/each}
      </div>
    </div>
  </section>

  <section>
    <SectionHeader title="Course Search"
      sub="Search by course name, ID, or topic tag. Results appear after 3 characters." />
    <div class="search-wrap">
      <div class="search-input-row">
        <input class="search-input" type="text" bind:value={courseSearch}
          placeholder="e.g. data structures, ACE, CSCE 156, biology..." />
        {#if courseSearch.length > 0}
          <button class="clear-btn" on:click={() => courseSearch = ''}>×</button>
        {/if}
      </div>
      {#if courseSearch.length > 0 && courseSearch.length < 3}
        <p class="hint">Keep typing…</p>
      {/if}
      {#if courseResults.length > 0}
        <div class="search-results">
          {#each courseResults as c}
            <div class="course-result">
              <div class="course-result-top">
                <span class="badge blue">{c.course_id}</span>
                <span class="course-name">{c.name}</span>
                <span class="muted cr-meta">{c.credit_hours} cr</span>
              </div>
              {#if c.tags.length}
                <div class="tag-row">
                  {#each c.tags.slice(0,5) as t}
                    <span class="mini-tag">{t}</span>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {:else if courseSearch.length >= 3}
        <p class="hint">No matching courses found.</p>
      {/if}
    </div>
  </section>

  {#if recommendedCourses.length > 0}
    <section>
      <SectionHeader title="Recommended Courses"
        sub="Based on your interest tags — courses you're not yet enrolled in." />
      <div class="rec-grid">
        {#each recommendedCourses as c}
          <div class="card rec-card">
            <div class="rec-top">
              <span class="badge blue">{c.course_id}</span>
              <span class="muted">{c.credit_hours} cr</span>
            </div>
            <strong>{c.name}</strong>
            <small class="muted">{c.program_id}</small>
            <div class="tag-row">
              {#each c.tags.slice(0,5) as t}
                <span class="mini-tag">{t}</span>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  {#if suggestedClubs.length > 0}
    <section>
      <SectionHeader title="Clubs & Activities You Might Like"
        sub="Matched to your interest tags." />
      <div class="resource-grid">
        {#each suggestedClubs as a}
          <div class="card resource-card">
            <div class="resource-type">Club</div>
            <strong>{a.name}</strong>
            <small class="muted">{a.location?.name ?? ''}</small>
            {#if a.meet_day}
              <span class="badge">{a.meet_day} · {a.meet_time}</span>
            {/if}
          </div>
        {/each}
      </div>
    </section>
  {/if}

  <section>
    <SectionHeader title="Recent Campus Visits" />
    <div class="card">
      {#each visits.slice(0,10) as v}
        <div class="visit-row">
          <div>
            <strong>{v.activity?.name ?? '—'}</strong>
            <span class="muted">{v.location?.name ?? '—'}</span>
          </div>
          <div class="visit-right">
            <span class="badge">{v.location?.type ?? '—'}</span>
            <span>{v.duration_minutes} min</span>
            <small class="muted">{new Date(v.date).toLocaleDateString()}</small>
          </div>
        </div>
      {:else}
        <p class="empty">No visits recorded yet.</p>
      {/each}
    </div>
  </section>

  <section>
    <SectionHeader title="Campus Reviews"
      sub="See what students think about locations and activities." />

    <div class="review-section-label">Locations</div>
    <div class="review-grid">
      {#each locationsWithReviews.filter(l => l.reviewCount > 0).sort((a,b) => b.avgRating - a.avgRating).slice(0,6) as l}
        <div class="card review-card">
          <div class="review-name">{l.name}</div>
          <div class="review-type">{l.type}</div>
          {#if l.avgRating}
            <div class="rating-row">
              <span class="stars">{'⭐'.repeat(Math.round(l.avgRating))}</span>
              <span class="rating-num">{l.avgRating} <small>({l.reviewCount})</small></span>
            </div>
          {/if}
          {#if l.recentTexts.length}
            <p class="review-quote">"{l.recentTexts[l.recentTexts.length-1]}"</p>
          {/if}
        </div>
      {/each}
    </div>

    <div class="review-section-label">Activities & Clubs</div>
    <div class="review-grid">
      {#each activitiesWithReviews.filter(a => a.reviewCount > 0).sort((a,b) => b.avgRating - a.avgRating).slice(0,6) as a}
        <div class="card review-card">
          <div class="review-name">{a.name}</div>
          <div class="review-type">{a.type}</div>
          {#if a.avgRating}
            <div class="rating-row">
              <span class="stars">{'⭐'.repeat(Math.round(a.avgRating))}</span>
              <span class="rating-num">{a.avgRating} <small>({a.reviewCount})</small></span>
            </div>
          {/if}
          {#if a.recentTexts.length}
            <p class="review-quote">"{a.recentTexts[a.recentTexts.length-1]}"</p>
          {/if}
        </div>
      {/each}
    </div>

    <div class="card review-form">
      <div class="card-label">Leave a Review</div>
      <div class="review-target-tabs">
        <button class="term-btn" class:active={reviewTarget==='location'}
          on:click={() => reviewTarget='location'}>Location</button>
        <button class="term-btn" class:active={reviewTarget==='activity'}
          on:click={() => reviewTarget='activity'}>Activity / Club</button>
      </div>

      {#if reviewTarget === 'location'}
        <select class="select" bind:value={reviewLocId}>
          <option value="">— select a location —</option>
          {#each sortedLocations as l}
            <option value={l.location_id}>
              {visitedLocs.has(l.location_id) ? '✓ ' : ''}{l.name}
            </option>
          {/each}
        </select>
      {:else}
        <select class="select" bind:value={reviewActId}>
          <option value="">— select an activity —</option>
          {#each sortedActivities as a}
            <option value={a.activity_id}>
              {visitedActs.has(a.activity_id) ? '✓ ' : ''}{a.name}
            </option>
          {/each}
        </select>
      {/if}

      <div class="star-row">
        {#each [1,2,3,4,5] as n}
          <button class="star-btn" class:lit={reviewRating >= n}
            on:click={() => reviewRating = n}>★</button>
        {/each}
        {#if reviewRating > 0}
          <span class="muted">{reviewRating}/5</span>
        {/if}
      </div>

      <textarea class="textarea" bind:value={reviewText}
        placeholder="Optional — share what you thought..." rows="3"></textarea>

      <button class="btn-submit" on:click={submitReview}
        disabled={reviewLoading || !reviewRating ||
          (reviewTarget==='location' && !reviewLocId) ||
          (reviewTarget==='activity' && !reviewActId)}>
        {reviewLoading ? 'Submitting…' : 'Submit Review'}
      </button>
    </div>

    {#if myReviews.length > 0}
      <div class="card">
        <div class="card-label">Your Reviews This Session</div>
        {#each myReviews as r}
          <div class="my-review-row">
            <div>
              <strong>{r.target_name}</strong>
              <small class="muted">{r.target_type}</small>
            </div>
            <div class="my-review-right">
              <span>{'⭐'.repeat(r.rating)}</span>
              {#if r.review_text}<p class="review-quote">"{r.review_text}"</p>{/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <section>
    <SectionHeader title="Tutoring Resources" sub="Drop-in tutoring centers available on campus." />
    {#if avgScore !== null && avgScore < 75}
      <div class="alert">
        📈 Your average is <strong>{avgScore}</strong>. Students who visit tutoring typically score 8–12 points higher.
      </div>
    {/if}
    <div class="resource-grid">
      {#each tutoring as t}
        <div class="card resource-card">
          <div class="resource-type">Tutoring</div>
          <strong>{t.name}</strong>
          <small class="muted">{t.location?.name ?? ''}</small>
          {#if t.meet_day}<span class="badge">{t.meet_day} · {t.meet_time}</span>{/if}
        </div>
      {/each}
    </div>
  </section>

</PageShell>

{#if reviewToast}
  <div class="toast">{reviewToast}</div>
{/if}

<style>
  .stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.85rem; }
  section    { display:flex; flex-direction:column; gap:.85rem; }

  .chart-grid-3 {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: .85rem;
  }

  .courses-layout {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 1.25rem;
    align-items: start;
  }
  .term-sidebar { display:flex; flex-direction:column; gap:.35rem; }
  .term-label   { font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin-bottom:.2rem; }
  .pill-grid    { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:.65rem; }

  .rec-grid      { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:.85rem; }
  .resource-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:.75rem; }
  .review-grid   { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:.75rem; }

  .card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); padding:1.25rem 1.4rem; box-shadow:var(--shadow);
  }
  .card-label {
    font-size:.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted); margin-bottom:.85rem;
  }

  .course-card   { display:flex; flex-direction:column; gap:.35rem; }
  .resource-card { display:flex; flex-direction:column; gap:.35rem; }
  .resource-type { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--red); }

  .rec-card { display:flex; flex-direction:column; gap:.4rem; }
  .rec-top  { display:flex; justify-content:space-between; align-items:center; }
  .rec-card strong { font-size:.92rem; }

  .term-btn {
    padding:.3rem .75rem; border-radius:999px; text-align:left;
    border:1px solid var(--border); background:var(--surface);
    font-size:.8rem; cursor:pointer; transition:all .15s; color:var(--muted);
    white-space:nowrap;
  }
  .term-btn.active { background:var(--red); color:#fff; border-color:var(--red); }

  .search-wrap      { max-width:100%; }
  .search-input-row { display:flex; align-items:center; gap:.5rem; }
  .search-input {
    flex:1; padding:.7rem 1rem;
    border:1.5px solid var(--border); border-radius:8px;
    font-family:var(--font-sans); font-size:.92rem;
    background:var(--surface); color:var(--ink);
    outline:none; transition:border-color .15s;
  }
  .search-input:focus { border-color:var(--red); }
  .clear-btn {
    width:32px; height:32px; border-radius:50%;
    border:1px solid var(--border); background:var(--surface);
    cursor:pointer; font-size:1.1rem; color:var(--muted);
    display:flex; align-items:center; justify-content:center;
    transition:all .15s; flex-shrink:0;
  }
  .clear-btn:hover { background:var(--red); color:#fff; border-color:var(--red); }
  .hint { font-size:.8rem; color:var(--muted); margin-top:.35rem; }
  .search-results {
    border:1px solid var(--border); border-radius:8px;
    background:var(--surface); box-shadow:var(--shadow-lg); margin-top:.4rem; overflow:hidden;
  }
  .course-result {
    padding:.75rem 1.1rem; border-bottom:1px solid var(--border); transition:background .1s;
    display:flex; flex-direction:column; gap:.35rem;
  }
  .course-result:last-child { border-bottom:none; }
  .course-result:hover { background:var(--cream); }
  .course-result-top { display:flex; align-items:center; gap:.65rem; }
  .course-name { font-size:.88rem; color:var(--ink); flex:1; }
  .cr-meta     { white-space:nowrap; }
  .tag-row     { display:flex; gap:.3rem; flex-wrap:wrap; }
  .mini-tag {
    font-size:.68rem; font-family:var(--font-mono);
    background:var(--cream); border:1px solid var(--border);
    border-radius:999px; padding:.1rem .45rem; color:var(--muted);
  }

  .review-section-label {
    font-size:.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.07em; color:var(--muted);
  }
  .review-card  { display:flex; flex-direction:column; gap:.4rem; }
  .review-name  { font-weight:700; font-size:.95rem; }
  .review-type  { font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
  .rating-row   { display:flex; align-items:center; gap:.5rem; margin-top:.1rem; }
  .stars        { font-size:.85rem; }
  .rating-num   { font-size:.85rem; font-weight:600; }
  .rating-num small { font-weight:400; color:var(--muted); }
  .review-quote { font-size:.82rem; color:var(--muted); font-style:italic; line-height:1.4; margin:0; }

  .review-form        { display:flex; flex-direction:column; gap:.85rem; max-width:560px; }
  .review-target-tabs { display:flex; gap:.4rem; }
  .select {
    width:100%; padding:.65rem .9rem;
    border:1.5px solid var(--border); border-radius:8px;
    font-family:var(--font-sans); font-size:.9rem;
    background:var(--surface); color:var(--ink);
    outline:none; cursor:pointer; transition:border-color .15s;
  }
  .select:focus { border-color:var(--red); }
  .star-row { display:flex; align-items:center; gap:.25rem; }
  .star-btn { background:none; border:none; cursor:pointer; font-size:1.9rem; color:#ddd; line-height:1; transition:color .1s; padding:0; }
  .star-btn.lit { color:#f0a500; }
  .textarea {
    width:100%; padding:.7rem 1rem;
    border:1.5px solid var(--border); border-radius:8px;
    font-family:var(--font-sans); font-size:.9rem;
    background:var(--surface); color:var(--ink);
    outline:none; resize:vertical; transition:border-color .15s;
  }
  .textarea:focus { border-color:var(--red); }
  .btn-submit {
    padding:.75rem 1.5rem; background:var(--red); color:#fff;
    border:none; border-radius:8px; font-family:var(--font-sans);
    font-size:.9rem; font-weight:600; cursor:pointer; transition:background .15s;
    align-self:flex-start;
  }
  .btn-submit:hover:not(:disabled) { background:var(--red-dark); }
  .btn-submit:disabled { opacity:.45; cursor:not-allowed; }

  .my-review-row {
    display:flex; justify-content:space-between; align-items:flex-start;
    gap:1rem; padding:.65rem 0; border-bottom:1px solid var(--border);
  }
  .my-review-row:last-child { border-bottom:none; }
  .my-review-row strong { display:block; font-size:.9rem; }
  .my-review-right { text-align:right; flex-shrink:0; }

  .visit-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:.65rem 0; border-bottom:1px solid var(--border); gap:1rem;
  }
  .visit-row:last-child { border-bottom:none; }
  .visit-row strong { display:block; font-size:.9rem; }
  .visit-right { display:flex; align-items:center; gap:.6rem; font-size:.85rem; white-space:nowrap; }

  .alert {
    padding:.9rem 1.1rem; background:#fdf3e0;
    border:1px solid #f0cf88; border-radius:var(--radius);
    font-size:.88rem; color:var(--amber);
  }

  .chart-note { font-size:.75rem; color:var(--muted); font-style:italic; margin:.4rem 0 0; }
  .muted { color:var(--muted); font-size:.82rem; }
  .empty { color:var(--muted); font-size:.9rem; padding:1rem 0; }

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

  @media (max-width:900px) {
    .chart-grid-3   { grid-template-columns:1fr 1fr; }
    .courses-layout { grid-template-columns:1fr; }
    .term-sidebar   { flex-direction:row; flex-wrap:wrap; }
  }
  @media (max-width:600px) {
    .chart-grid-3 { grid-template-columns:1fr; }
  }
</style>
