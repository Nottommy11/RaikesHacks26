import { gql } from '$lib/hasura.js';

export async function load() {
  const [aggs, flat, tagData] = await Promise.all([
    gql(`query AdminAggs {
      solo:     exam_attempts_aggregate(where: { study_mode: { _eq: "Solo" } })     { aggregate { avg { score } count } }
      group_s:  exam_attempts_aggregate(where: { study_mode: { _eq: "Group" } })    { aggregate { avg { score } count } }
      tutoring: exam_attempts_aggregate(where: { study_mode: { _eq: "Tutoring" } }) { aggregate { avg { score } count } }
      online:   exam_attempts_aggregate(where: { study_mode: { _eq: "Online" } })   { aggregate { avg { score } count } }
      tutoring_visitors:     exam_attempts_aggregate(where: { study_mode: { _eq:  "Tutoring" } }) { aggregate { avg { score } count } }
      non_tutoring_visitors: exam_attempts_aggregate(where: { study_mode: { _neq: "Tutoring" } }) { aggregate { avg { score } count } }
      users_aggregate   { aggregate { count } }
      visits_aggregate  { aggregate { count } }
      reviews_aggregate { aggregate { avg { rating } count } }
    }`),

    gql(`query FlatData {
      locations  { location_id name type }
      visits     { visit_id user_id activity_id location_id duration_minutes date }
      reviews    { review_id location_id rating }
      activities { activity_id name type location_id }
      exam_attempts { user_id score study_mode pre_mood post_mood created_at }
    }`),

    gql(`query TagData {
      user_interests { tag_id }
      course_tags {
        tag_id
        course { course_id name program_id }
      }
      activity_tags {
        tag_id
        activity { activity_id name type }
      }
    }`)
  ]);

  // Location stats
  const locMap = {};
  for (const l of (flat.locations ?? [])) {
    locMap[l.location_id] = { ...l, visitCount: 0, totalMinutes: 0, ratings: [] };
  }
  for (const v of (flat.visits ?? [])) {
    if (locMap[v.location_id]) {
      locMap[v.location_id].visitCount++;
      locMap[v.location_id].totalMinutes += v.duration_minutes ?? 0;
    }
  }
  for (const r of (flat.reviews ?? [])) {
    if (r.location_id && locMap[r.location_id]) {
      locMap[r.location_id].ratings.push(r.rating);
    }
  }
  const locations = Object.values(locMap)
  .map(l => ({
    ...l,
    avgDuration: l.visitCount ? Math.round(l.totalMinutes / l.visitCount) : 0,
             avgRating:   l.ratings.length
             ? (l.ratings.reduce((a,b)=>a+b,0)/l.ratings.length).toFixed(1)
             : null,
             reviewCount: l.ratings.length,
  }))
  .sort((a,b) => b.visitCount - a.visitCount);

  // Activity stats
  const actVisits = {}, actMins = {};
  for (const v of (flat.visits ?? [])) {
    actVisits[v.activity_id] = (actVisits[v.activity_id] ?? 0) + 1;
    actMins[v.activity_id]   = (actMins[v.activity_id]   ?? 0) + (v.duration_minutes ?? 0);
  }
  const activities = (flat.activities ?? [])
  .map(a => ({
    ...a,
    location:    locMap[a.location_id] ?? null,
    visitCount:  actVisits[a.activity_id] ?? 0,
    avgDuration: actVisits[a.activity_id]
    ? Math.round(actMins[a.activity_id] / actVisits[a.activity_id])
    : 0,
  }))
  .sort((a,b) => b.visitCount - a.visitCount)
  .slice(0, 10);

  // Tag trends
  const tagCount = {}, tagCourses = {}, tagActivities = {};
  for (const i of (tagData.user_interests ?? [])) {
    tagCount[i.tag_id] = (tagCount[i.tag_id] ?? 0) + 1;
  }
  for (const ct of (tagData.course_tags ?? [])) {
    if (!ct.course) continue;
    tagCourses[ct.tag_id] = tagCourses[ct.tag_id] ?? [];
    tagCourses[ct.tag_id].push(ct.course);
  }
  for (const at of (tagData.activity_tags ?? [])) {
    if (!at.activity) continue;
    tagActivities[at.tag_id] = tagActivities[at.tag_id] ?? [];
    tagActivities[at.tag_id].push(at.activity);
  }
  const tagTrends = Object.entries(tagCount)
  .map(([tag, count]) => ({
    tag, count,
    courses:    (tagCourses[tag]    ?? []).slice(0, 8),
                          activities: (tagActivities[tag] ?? []).slice(0, 6),
  }))
  .sort((a,b) => b.count - a.count)
  .slice(0, 20);

  const safeAvg   = agg => agg?.aggregate?.avg?.score?.toFixed(1) ?? '0';
  const safeCount = agg => agg?.aggregate?.count ?? 0;

  const studyModes = [
    { label:'Solo',     avg:safeAvg(aggs.solo),     count:safeCount(aggs.solo) },
    { label:'Group',    avg:safeAvg(aggs.group_s),  count:safeCount(aggs.group_s) },
    { label:'Tutoring', avg:safeAvg(aggs.tutoring), count:safeCount(aggs.tutoring) },
    { label:'Online',   avg:safeAvg(aggs.online),   count:safeCount(aggs.online) },
  ];

  const tAvg = safeAvg(aggs.tutoring_visitors);
  const ntAvg = safeAvg(aggs.non_tutoring_visitors);
  const lift = (parseFloat(tAvg) - parseFloat(ntAvg)).toFixed(1);

  // Chart-specific data
  const visitsForCharts = (flat.visits ?? []).map(v => ({
    date:             v.date,
    duration_minutes: v.duration_minutes,
    location_id:      v.location_id,
  }));

  const locationTypes = Object.fromEntries(
    (flat.locations ?? []).map(l => [l.location_id, l.type])
  );

  const attemptsForCharts = (flat.exam_attempts ?? []).map(a => ({
    score:      a.score,
    pre_mood:   a.pre_mood,
    post_mood:  a.post_mood,
    created_at: a.created_at,
    study_mode: a.study_mode,
  }));

  return {
    locations, tagTrends, studyModes, activities,
    visitsForCharts, locationTypes, attemptsForCharts,
    tutoringAvg:    tAvg,
    nonTutoringAvg: ntAvg,
    lift:           parseFloat(lift) > 0 ? `+${lift}` : lift,
    totalUsers:     safeCount(aggs.users_aggregate),
    totalVisits:    safeCount(aggs.visits_aggregate),
    avgRating:      aggs.reviews_aggregate?.aggregate?.avg?.rating?.toFixed(1) ?? '—',
    totalReviews:   safeCount(aggs.reviews_aggregate),
  };
}
