import { gql } from '$lib/hasura.js';
import { error } from '@sveltejs/kit';

export async function load({ url }) {
  const uid = url.searchParams.get('uid');
  if (!uid) throw error(400, 'Missing uid');

  const [userData, globalData] = await Promise.all([
    gql(`
      query UserInterestData($uid: uuid!) {
        users_by_pk(user_id: $uid) {
          user_id first_name last_name nuid
        }
        user_interests(where: { user_id: { _eq: $uid } }) {
          interest_id tag_id
        }
        enrollment(where: { user_id: { _eq: $uid } }) {
          course_id
        }
        declared_programs(where: { user_id: { _eq: $uid } }) {
          program_id type
        }
      }
    `, { uid }),

    gql(`
      query GlobalData {
        tags { tag_id }
        user_interests { tag_id }
        course_tags { course_id tag_id }
        activity_tags { activity_id tag_id }
      }
    `)
  ]);

  if (!userData.users_by_pk) throw error(404, 'User not found');

  const profile       = userData.users_by_pk;
  const myTags        = userData.user_interests ?? [];
  const myTagIds      = new Set(myTags.map(t => t.tag_id));
  const allTags       = (globalData.tags ?? []).map(t => t.tag_id).sort();
  const enrolledCourseIds = new Set((userData.enrollment ?? []).map(e => e.course_id));

  // Global tag popularity
  const tagPop = {};
  for (const i of (globalData.user_interests ?? [])) {
    tagPop[i.tag_id] = (tagPop[i.tag_id] ?? 0) + 1;
  }

  // Tags associated with enrolled courses
  const courseTagScores = {};
  for (const ct of (globalData.course_tags ?? [])) {
    if (enrolledCourseIds.has(ct.course_id)) {
      courseTagScores[ct.tag_id] = (courseTagScores[ct.tag_id] ?? 0) + 3; // course match = high weight
    }
  }

  // Blend with popularity
  const suggestions = allTags
    .filter(t => !myTagIds.has(t))
    .map(t => ({
      tag:   t,
      score: (courseTagScores[t] ?? 0) + (tagPop[t] ?? 0) * 0.5,
    }))
    .filter(t => t.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 12)
    .map(t => t.tag);

  // If not enough scored suggestions, pad with popular tags
  if (suggestions.length < 10) {
    const popular = Object.entries(tagPop)
      .filter(([t]) => !myTagIds.has(t) && !suggestions.includes(t))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10 - suggestions.length)
      .map(([t]) => t);
    suggestions.push(...popular);
  }

  return {
    uid,
    profile,
    myTags,
    allTags,
    suggestions,
    programs: userData.declared_programs ?? [],
  };
}
