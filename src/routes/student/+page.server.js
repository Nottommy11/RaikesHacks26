import { gql } from '$lib/hasura.js';
import { error } from '@sveltejs/kit';

export async function load({ url }) {
  const uid = url.searchParams.get('uid');
  if (!uid) throw error(400, 'Missing uid');

  const [userData, refData, activityData, courseData] = await Promise.all([
    gql(`
    query StudentData($uid: uuid!) {
      users_by_pk(user_id: $uid) {
        user_id first_name last_name nuid
      }
      enrollment(where: { user_id: { _eq: $uid } }) {
        enroll_id course_id term
      }
      exam_attempts(
        where: { user_id: { _eq: $uid } }
        order_by: { created_at: asc }
      ) {
        attempt_id exam_id score study_mode pre_mood post_mood created_at
      }
      visits(
        where: { user_id: { _eq: $uid } }
        order_by: { date: desc }
      ) {
        visit_id activity_id location_id date duration_minutes
      }
      user_interests(where: { user_id: { _eq: $uid } }) {
        tag_id
      }
      reviews(where: { user_id: { _eq: $uid } }) {
        review_id location_id activity_id rating review_text created_at
      }
    }
    `, { uid }),

    gql(`
    query RefData {
      exams      { exam_id name type course_id }
      locations  { location_id name type }
      activities { activity_id name type meet_day meet_time location_id }
      activity_tags { activity_id tag_id }
      reviews(order_by: { created_at: desc }) {
        review_id location_id activity_id rating review_text
      }
    }
    `),

    gql(`
    query ActivityData {
      tutoring_activities: activities(where: { type: { _eq: "tutoring" } }) {
        activity_id name type meet_day meet_time location_id
      }
      club_activities: activities(where: { type: { _eq: "club" } }, limit: 50) {
        activity_id name meet_day meet_time location_id
        activity_tags { tag_id }
      }
    }
    `),

    gql(`
    query CourseData {
      courses {
        course_id name program_id credit_hours
        course_tags { tag_id }
      }
    }
    `)
  ]);

  if (!userData.users_by_pk) throw error(404, 'User not found');

  const profile    = userData.users_by_pk;
  const enrollment = userData.enrollment ?? [];
  const myReviews  = userData.reviews ?? [];

  // Lookup maps
  const examMap = Object.fromEntries((refData.exams     ?? []).map(e => [e.exam_id,     e]));
  const locMap  = Object.fromEntries((refData.locations ?? []).map(l => [l.location_id, l]));
  const actMap  = Object.fromEntries((refData.activities ?? []).map(a => [a.activity_id, a]));

  // Enrich attempts
  const attempts = (userData.exam_attempts ?? []).map(a => ({
    ...a,
    exam: examMap[a.exam_id] ?? null,
  }));

  // Enrich visits
  const visits = (userData.visits ?? []).map(v => ({
    ...v,
    location: locMap[v.location_id] ?? null,
    activity: actMap[v.activity_id] ?? null,
  }));

  // Terms
  const allTerms    = [...new Set(enrollment.map(e => e.term))].sort().reverse();
  const latestTerm  = allTerms[0] ?? null;

  // Stats
  const scores   = attempts.map(a => a.score).filter(Boolean);
  const avgScore = scores.length
  ? Math.round(scores.reduce((a,b) => a+b,0) / scores.length)
  : null;

  const modeCount = {};
  for (const a of attempts) {
    modeCount[a.study_mode] = (modeCount[a.study_mode] ?? 0) + 1;
  }

  const visitsByType = {};
  for (const v of visits) {
    const t = v.location?.type ?? 'Other';
    visitsByType[t] = (visitsByType[t] ?? 0) + (v.duration_minutes ?? 0);
  }

  // Interests
  const interests   = (userData.user_interests ?? []).map(i => i.tag_id);
  const interestSet = new Set(interests);

  // Tutoring + club suggestions
  const tutoring = (activityData.tutoring_activities ?? []).map(a => ({
    ...a, location: locMap[a.location_id] ?? null,
  }));

  const suggestedClubs = (activityData.club_activities ?? [])
  .map(a => ({
    ...a,
    location: locMap[a.location_id] ?? null,
    tags: a.activity_tags?.map(t => t.tag_id) ?? [],
  }))
  .filter(a => a.tags.some(t => interestSet.has(t)))
  .sort((a,b) => {
    const aScore = a.tags.filter(t => interestSet.has(t)).length;
    const bScore = b.tags.filter(t => interestSet.has(t)).length;
    return bScore - aScore;
  })
  .slice(0, 8);

  // Course recommendations — unenrolled, scored by tag overlap
  const enrolledIds = new Set(enrollment.map(e => e.course_id));
  const recommendedCourses = (courseData.courses ?? [])
  .map(c => {
    const courseTags = c.course_tags?.map(t => t.tag_id) ?? [];
    const overlap    = courseTags.filter(t => interestSet.has(t)).length;
    return { ...c, tags: courseTags, overlap, enrolled: enrolledIds.has(c.course_id) };
  })
  .filter(c => c.overlap > 0 && !c.enrolled)
  .sort((a,b) => b.overlap - a.overlap)
  .slice(0, 12);

  // Location review summaries (anonymous aggregates)
  const locReviews = {};
  for (const r of (refData.reviews ?? [])) {
    if (!r.location_id) continue;
    locReviews[r.location_id] = locReviews[r.location_id] ?? { ratings: [], texts: [] };
    locReviews[r.location_id].ratings.push(r.rating);
    if (r.review_text) locReviews[r.location_id].texts.push(r.review_text);
  }

  // Activity review summaries
  const actReviews = {};
  for (const r of (refData.reviews ?? [])) {
    if (!r.activity_id) continue;
    actReviews[r.activity_id] = actReviews[r.activity_id] ?? { ratings: [], texts: [] };
    actReviews[r.activity_id].ratings.push(r.rating);
    if (r.review_text) actReviews[r.activity_id].texts.push(r.review_text);
  }

  // Locations with review data — for review form + display
  const locationsWithReviews = (refData.locations ?? []).map(l => ({
    ...l,
    avgRating:   locReviews[l.location_id]?.ratings.length
    ? (locReviews[l.location_id].ratings.reduce((a,b)=>a+b,0) / locReviews[l.location_id].ratings.length).toFixed(1)
    : null,
    reviewCount: locReviews[l.location_id]?.ratings.length ?? 0,
    recentTexts: (locReviews[l.location_id]?.texts ?? []).slice(-3),
  }));

  const activitiesWithReviews = (refData.activities ?? []).map(a => ({
    ...a,
    location: locMap[a.location_id] ?? null,
    avgRating:   actReviews[a.activity_id]?.ratings.length
    ? (actReviews[a.activity_id].ratings.reduce((a,b)=>a+b,0) / actReviews[a.activity_id].ratings.length).toFixed(1)
    : null,
    reviewCount: actReviews[a.activity_id]?.ratings.length ?? 0,
    recentTexts: (actReviews[a.activity_id]?.texts ?? []).slice(-3),
  }));

  // Visited location/activity IDs for review form ordering
  const visitedLocationIds  = new Set(visits.map(v => v.location_id).filter(Boolean));
  const visitedActivityIds  = new Set(visits.map(v => v.activity_id).filter(Boolean));
  const reviewedLocationIds = new Set(myReviews.map(r => r.location_id).filter(Boolean));
  const reviewedActivityIds = new Set(myReviews.map(r => r.activity_id).filter(Boolean));

  return {
    uid, profile, enrollment, attempts, visits,
    interests, tutoring, suggestedClubs,
    avgScore, modeCount, visitsByType,
    allTerms, latestTerm,
    recommendedCourses,
    locationsWithReviews,
    activitiesWithReviews,
    visitedLocationIds:  [...visitedLocationIds],
    visitedActivityIds:  [...visitedActivityIds],
    reviewedLocationIds: [...reviewedLocationIds],
    reviewedActivityIds: [...reviewedActivityIds],
    allCourses: (courseData.courses ?? []).map(c => ({
      course_id: c.course_id,
      name:      c.name,
      program_id: c.program_id,
      credit_hours: c.credit_hours,
      tags:      c.course_tags?.map(t => t.tag_id) ?? [],
    })),
  };
}
