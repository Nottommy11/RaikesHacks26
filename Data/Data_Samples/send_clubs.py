import csv
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

# --- 1. THE DATA ---
LOCATIONS = [
    ("Abel Dining Hall", "Dining"), ("Cather Dining Hall", "Dining"),
    ("Hamilton Hall", "Academic"), ("Avery Hall", "Academic"),
    ("Love Library", "Study"), ("DLC Exam Commons", "Testing"),
    ("North 17th Parking Garage", "Parking"), ("East Campus", "Zone"),
    ("Chase Hall", "Academic"), ("Jorgensen Hall", "Academic"),
    ("Kiewit Hall", "Academic"), ("Scott Hall", "Residential"),
    ("Abel Hall", "Residential"), ("Nebraska Hall", "Academic"),
    ("Othmer Hall", "Academic"), ("Louise Pound Hall", "Academic"),
    ("14th St Parking Garage", "Parking"), ("Carolyn Pope Edwards Hall", "Academic"),
    ("Sapp Recreation Facility", "Recreation"), ("Burnett Hall", "Academic"),
    ("Brace Laboratory", "Academic"), ("Manter Hall", "Academic"),
    ("Nebraska Union", "Dining/General"), ("Selleck Building", "Dining")
]

# We will load the clubs from the CSV we generated earlier
CLUBS_CSV = "CLUBS_CLEAN.csv"

def seed_database():
    print("Fetching/Inserting Locations...")

    # GraphQL Mutations
    insert_loc_mutation = """
    mutation InsertLocation($name: String!, $type: String!) {
      insert_locations_one(object: {name: $name, type: $type}) { location_id }
    }
    """

    # Fetch existing locations to avoid duplicates
    existing_locs = run_query("query { locations { location_id name } }")['data']['locations']
    loc_dict = {loc['name']: loc['location_id'] for loc in existing_locs}

    # Insert missing locations
    for name, loc_type in LOCATIONS:
        if name not in loc_dict:
            res = run_query(insert_loc_mutation, {"name": name, "type": loc_type})
            loc_dict[name] = res['data']['insert_locations_one']['location_id']
            print(f"Inserted Location: {name} ({loc_type})")

    # Helper function to map clubs to buildings logically
    def get_logical_location(club_name, tags):
        tags_str = tags.lower()
        if "engineering" in tags_str or "robotics" in tags_str or "aerospace" in tags_str:
            return loc_dict.get("Othmer Hall") or loc_dict.get("Kiewit Hall")
        if "biology" in tags_str or "pre-med" in tags_str or "health" in tags_str:
            return loc_dict.get("Manter Hall")
        if "chemistry" in tags_str or "science" in tags_str:
            return loc_dict.get("Hamilton Hall")
        if "agriculture" in tags_str or "agronomy" in tags_str:
            return loc_dict.get("Chase Hall")
        if "computer science" in tags_str or "programming" in tags_str:
            return loc_dict.get("Avery Hall")

        # Fallback for general/business/humanities clubs
        return loc_dict.get("Nebraska Union")

    print("\nInserting Clubs and Tags...")

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

    try:
        with open(CLUBS_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['Club Name'].strip()
                meet_day = row.get('Meeting Day', '')
                meet_time = row.get('Meeting Time', '')
                tags_list = row.get('Tags', '').split(',')

                # 1. Determine location
                location_id = get_logical_location(name, row.get('Tags', ''))

                # 2. Insert Activity (Club)
                act_res = run_query(insert_activity_mutation, {
                    "name": name,
                    "type": "club",
                    "location_id": location_id,
                    "meet_day": meet_day,
                    "meet_time": meet_time
                })
                activity_id = act_res['data']['insert_activities_one']['activity_id']

                # 3. Insert and Link Tags
                for tag in tags_list:
                    tag_name = tag.strip().lower()
                    if not tag_name: continue

                    # Upsert tag
                    run_query(insert_tag_mutation, {"tag_id": tag_name})
                    # Link to activity
                    run_query(insert_act_tag_mutation, {"activity_id": activity_id, "tag_id": tag_name})

                print(f"Inserted Club: {name}")

    except FileNotFoundError:
        print(f"Error: Make sure you saved the clubs data as {CLUBS_CSV}")

    print("\nInfrastructure complete!")

if __name__ == "__main__":
    seed_database()
