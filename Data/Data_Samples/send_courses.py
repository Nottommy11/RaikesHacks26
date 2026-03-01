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

ACE_CSV = "ACE_CLEAN.csv"
MAJOR_CSV = "MAJOR_CLEAN.csv"
DUPES_CSV = "duplicates.csv"

# A map of common prefixes to automatically generate your programs
PROGRAM_MAP = {
    "CSCE": "Computer Science and Engineering",
    "SOFT": "Software Engineering",
    "RAIK": "Raikes School",
    "BSEN": "Biological Systems Engineering",
    "MECH": "Mechanical Engineering",
    "ENGR": "College of Engineering",
    "MATH": "Mathematics",
    "STAT": "Statistics",
    "PHYS": "Physics",
    "CHEM": "Chemistry",
    "BIOC": "Biochemistry",
    "LIFE": "Biological Sciences",
    "ECON": "Economics",
    "BSAD": "Business Administration",
    "ENGL": "English",
    "HIST": "History",
    "PHIL": "Philosophy",
    "POLS": "Political Science",
    "PSYC": "Psychology",
    "SOCI": "Sociology",
    "COMM": "Communication Studies",
    "CRIM": "Criminology and Criminal Justice",
    "ANTH": "Anthropology",
    "ARCH": "Architecture",
    "DSGN": "Design",
    "MUSC": "Music",
    "THEA": "Theatre Arts",
    "FILM": "Film Studies"
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
            # We now raise an exception so it stops immediately if something is wrong!
            raise Exception(f"GraphQL Error with variables {variables}: {res['errors']}")
        return res
    else:
        raise Exception(f"Query failed: {request.status_code}. {request.text}")

def process_courses():
    insert_tag_mutation = """
    mutation InsertTag($tag_id: String!) {
      insert_tags_one(
        object: {tag_id: $tag_id},
        on_conflict: {constraint: tags_pkey, update_columns: []}
      ) { tag_id }
    }
    """

    fetch_courses_query = """
    query GetCourses { courses { course_id } }
    """
    response = run_query(fetch_courses_query)
    existing_courses = {c['course_id'] for c in response.get('data', {}).get('courses', [])}
    duplicates = []

    insert_program_mutation = """
    mutation InsertProgram($program_id: String!, $name: String!) {
      insert_programs_one(
        object: {program_id: $program_id, name: $name},
        on_conflict: {constraint: programs_pkey, update_columns: []}
      ) { program_id }
    }
    """

    insert_course_mutation = """
    mutation InsertCourse($course_id: String!, $name: String!, $credit_hours: Int, $program_id: String!) {
      insert_courses_one(
        object: {course_id: $course_id, name: $name, credit_hours: $credit_hours, program_id: $program_id},
        on_conflict: {constraint: courses_pkey, update_columns: []}
      ) { course_id }
    }
    """

    insert_course_tag_mutation = """
    mutation LinkCourseTag($course_id: String!, $tag_id: String!) {
      insert_course_tags_one(
        object: {course_id: $course_id, tag_id: $tag_id},
        on_conflict: {constraint: course_tags_pkey, update_columns: []}
      ) { course_id }
    }
    """

    def insert_row(course_id, name, credit_hours, tags_list):
        if course_id in existing_courses:
            duplicates.append([course_id, name, credit_hours, ", ".join(tags_list)])
            return

        # Extract the prefix (e.g., "CSCE") for the program_id
        prefix = course_id.split(' ')[0]
        program_name = PROGRAM_MAP.get(prefix, "General Studies")

        # 1. Insert Program (so the foreign key exists)
        run_query(insert_program_mutation, {"program_id": prefix, "name": program_name})

        # 2. Insert Course
        run_query(insert_course_mutation, {
            "course_id": course_id,
            "name": name,
            "credit_hours": credit_hours,
            "program_id": prefix
        })
        existing_courses.add(course_id)

        # 3. Link Course to existing Tags
        for tag_name in tags_list:
            tag_name = tag_name.strip().lower()
            if not tag_name: continue

            # Upsert the tag first so we guarantee the foreign key exists!
            run_query(insert_tag_mutation, {"tag_id": tag_name})

            # Now link them
            run_query(insert_course_tag_mutation, {"course_id": course_id, "tag_id": tag_name})

    # --- PROCESS ACE COURSES ---
    print("Processing ACE Courses...")
    try:
        with open(ACE_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ace_tag = f"ace {row['ACE']}"
                all_tags = [ace_tag] + row.get('Tags', '').split(',')

                try: ch = int(row.get('CH', 3))
                except ValueError: ch = 3

                insert_row(
                    course_id=row['Course Label'].strip(),
                    name=row['Name'].strip(),
                    credit_hours=ch,
                    tags_list=all_tags
                )
    except FileNotFoundError: print(f"Skipping {ACE_CSV} - not found.")

    # --- PROCESS MAJOR COURSES ---
    print("Processing Major Courses...")
    try:
        with open(MAJOR_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try: ch = int(row.get('CH', 3))
                except ValueError: ch = 3

                insert_row(
                    course_id=row['Course Label'].strip(),
                    name=row['Name'].strip(),
                    credit_hours=ch,
                    tags_list=row.get('Tags', '').split(',')
                )
    except FileNotFoundError: print(f"Skipping {MAJOR_CSV} - not found.")

    print("Database insertion complete!")

    if duplicates:
        print(f"Found {len(duplicates)} duplicates. Writing to {DUPES_CSV}...")
        with open(DUPES_CSV, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Course Label", "Name", "CH", "Tags"])
            writer.writerows(duplicates)

if __name__ == "__main__":
    process_courses()
