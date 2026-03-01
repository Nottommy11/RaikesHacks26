import { gql } from '$lib/hasura.js';

export async function load() {
  const data = await gql(`
    query LoginData {
      users(order_by: { last_name: asc }, limit: 100) {
        user_id
        first_name
        last_name
        nuid
      }
      admins(limit: 20) {
        admin_id
        username
        admin_type
      }
    }
  `);

  return {
    users:  data.users,
    admins: data.admins,
  };
}
