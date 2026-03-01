import requests
import os
from dotenv import load_dotenv

load_dotenv()
HASURA_ENDPOINT = os.getenv("HASURA_GRAPHQL_ENDPOINT")
HASURA_ADMIN_SECRET = os.getenv("HASURA_GRAPHQL_ADMIN_SECRET")

HEADERS = {
    "Content-Type": "application/json",
    "x-hasura-admin-secret": HASURA_ADMIN_SECRET
}

def run_query(query, variables=None):
    request = requests.post(
        HASURA_ENDPOINT,
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    if request.status_code == 200:
        res = request.json()
        if 'errors' in res:
            raise Exception(f"GraphQL Error with variables {variables}: {res['errors']}")
        return res
    else:
        raise Exception(f"Query failed: {request.status_code}. {request.text}")

# --- THE CLEANED TUTORING DATA ---
TUTORING_CENTERS = [
    {"name": "CAST Study Stop", "location": "Love Library", "meet_day": "Monday-Friday", "meet_time": "08:30 - 16:30", "tags": ["tutoring", "study strategies", "academic support"]},
    {"name": "NEST", "location": "Kiewit Hall", "meet_day": "Monday-Thursday", "meet_time": "18:00 - 21:00", "tags": ["engineering", "tutoring", "academic support"]},
    {"name": "Chemistry Resource Center", "location": "Hamilton Hall", "meet_day": "Monday-Friday", "meet_time": "08:00 - 19:00", "tags": ["chemistry", "tutoring"]},
    {"name": "CSCE Resource Center", "location": "Avery Hall", "meet_day": "Monday-Friday", "meet_time": "10:00 - 17:00", "tags": ["computer science", "programming", "tutoring"]},
    {"name": "Math Resource Center", "location": "Avery Hall", "meet_day": "Monday-Friday", "meet_time": "12:30 - 20:30", "tags": ["math", "tutoring"]},
    {"name": "Physics Resource Center", "location": "Jorgensen Hall", "meet_day": "Various", "meet_time": "Various", "tags": ["physics", "tutoring"]}
]

def process_tutoring():
    print("Fetching Locations...")

    # 1. Fetch locations to get UUIDs
    fetch_loc_query = "query { locations { location_id name } }"
    existing_locs = run_query(fetch_loc_query)['data']['locations']
    loc_dict = {loc['name']: loc['location_id'] for loc in existing_locs}

    # 2. Mutations
    insert_activity_mutation = """
    mutation InsertActivity($name: String!, $type: String!, $location_id: uuid!, $meet_day: String, $meet_time: String) {
      insert_activities_one(object: {
        name: $name, type: $type, location_id: $location_id, meet_day: $meet_day, meet_time: $meet_time
      }) { activity_id }
    }
    """

    insert_tag_mutation = """
    mutation InsertTag($tag_id: String!) {
      insert_tags_one(object: {tag_id: $tag_id}, on_conflict: {constraint: tags_pkey, update_columns: []}) { tag_id }
    }
    """

    insert_act_tag_mutation = """
    mutation LinkActivityTag($activity_id: uuid!, $tag_id: String!) {
      insert_activity_tags_one(object: {activity_id: $activity_id, tag_id: $tag_id}) { act_tag_id }
    }
    """

    print("Inserting Tutoring Centers...")
    for center in TUTORING_CENTERS:
        loc_name = center['location']
        location_id = loc_dict.get(loc_name)

        if not location_id:
            print(f"Warning: Location '{loc_name}' not found for {center['name']}. Skipping.")
            continue

        # Insert the Tutoring Center
        act_res = run_query(insert_activity_mutation, {
            "name": center['name'],
            "type": "tutoring",
            "location_id": location_id,
            "meet_day": center['meet_day'],
            "meet_time": center['meet_time']
        })
        activity_id = act_res['data']['insert_activities_one']['activity_id']

        # Insert and Link Tags
        for tag in center['tags']:
            tag_name = tag.strip().lower()
            if not tag_name: continue

            # Upsert tag (in case a new one like 'study strategies' wasn't in our previous list)
            run_query(insert_tag_mutation, {"tag_id": tag_name})

            # Link to activity
            run_query(insert_act_tag_mutation, {"activity_id": activity_id, "tag_id": tag_name})

        print(f"Successfully inserted: {center['name']}")

if __name__ == "__main__":
    process_tutoring()
