import { json } from '@sveltejs/kit';
import { gql } from '$lib/hasura.js';

export async function POST({ request }) {
  const { user_id, tag_id } = await request.json();
  if (!user_id || !tag_id) return json({ error: 'Missing user_id or tag_id' }, { status: 400 });

  // Check it doesn't already exist
  const existing = await gql(`
    query CheckInterest($uid: uuid!, $tid: String!) {
      user_interests(where: { user_id: { _eq: $uid }, tag_id: { _eq: $tid } }) {
        interest_id
      }
    }
  `, { uid: user_id, tid: tag_id });

  if (existing.user_interests.length > 0) {
    return json({ ok: true, skipped: true });
  }

  const now = new Date().toISOString();
  await gql(`
    mutation AddInterest($uid: uuid!, $tid: String!, $id: uuid!, $now: timestamptz!) {
      insert_user_interests_one(object: {
        interest_id: $id
        user_id: $uid
        tag_id: $tid
        created_at: $now
        updated_at: $now
      }) { interest_id }
    }
  `, {
    uid: user_id,
    tid: tag_id,
    id:  crypto.randomUUID(),
    now,
  });

  return json({ ok: true });
}

export async function DELETE({ request }) {
  const { user_id, tag_id } = await request.json();
  if (!user_id || !tag_id) return json({ error: 'Missing user_id or tag_id' }, { status: 400 });

  await gql(`
    mutation RemoveInterest($uid: uuid!, $tid: String!) {
      delete_user_interests(where: {
        user_id: { _eq: $uid }
        tag_id:  { _eq: $tid }
      }) { affected_rows }
    }
  `, { uid: user_id, tid: tag_id });

  return json({ ok: true });
}
