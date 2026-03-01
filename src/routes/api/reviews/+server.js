import { json } from '@sveltejs/kit';
import { gql } from '$lib/hasura.js';

export async function POST({ request }) {
    const { user_id, location_id, activity_id, rating, review_text } = await request.json();
    if (!user_id || !rating) return json({ error: 'Missing required fields' }, { status: 400 });
    if (!location_id && !activity_id) return json({ error: 'Need location_id or activity_id' }, { status: 400 });

    const now = new Date().toISOString();
    await gql(`
    mutation AddReview(
        $id: uuid!, $uid: uuid!, $lid: uuid, $aid: uuid,
        $rating: Int!, $text: String!, $now: timestamptz!
    ) {
        insert_reviews_one(object: {
            review_id:   $id
            user_id:     $uid
            location_id: $lid
            activity_id: $aid
            rating:      $rating
            review_text: $text
            created_at:  $now
            updated_at:  $now
        }) { review_id }
    }
    `, {
        id:     crypto.randomUUID(),
              uid:    user_id,
              lid:    location_id ?? null,
              aid:    activity_id ?? null,
              rating,
              text:   review_text ?? '',
              now,
    });

    return json({ ok: true });
}
