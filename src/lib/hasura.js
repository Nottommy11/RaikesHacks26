import { HASURA_URL, HASURA_ADMIN_SECRET } from '$env/static/private';

export async function gql(query, variables = {}) {
  const res = await fetch(HASURA_URL, {
    method: 'POST',
    headers: {
      'Content-Type':          'application/json',
      'x-hasura-admin-secret': HASURA_ADMIN_SECRET,
    },
    body: JSON.stringify({ query, variables }),
  });

  if (!res.ok) throw new Error(`Hasura HTTP ${res.status}`);

  const json = await res.json();
  if (json.errors) throw new Error(JSON.stringify(json.errors));

  return json.data;
}
