import csv
import random
import os
from faker import Faker

fake = Faker()
NUM_USERS = 50

# --- CONTEXTUAL REVIEW BANKS ---
REVIEWS = {
    "study": {
        "pos": ["Found a great quiet spot to study.", "Not too crowded today.", "Always my go-to spot between classes.", "Perfect lighting and fast Wi-Fi.", "Managed to snag a table with an outlet!", "Super productive vibe today."],
        "neg": ["Way too loud, couldn't focus.", "Every single table was taken.", "The Wi-Fi kept dropping.", "Too busy, had to leave.", "People were talking so loud.", "Couldn't find a single outlet."]
    },
    "dining": {
        "pos": ["Food was actually really good today!", "Line moved super fast.", "Great salad bar options.", "The pizza was fresh out of the oven.", "Staff was super friendly."],
        "neg": ["Line was out the door.", "Nowhere to sit during the lunch rush.", "Food was cold.", "They ran out of the good stuff.", "Tables were completely dirty."]
    },
    "club": {
        "pos": ["Awesome meeting, learned a lot about the projects.", "Really welcoming group of people!", "Great leadership and fun activities.", "Really cool project demo today.", "Free pizza was a massive plus."],
        "neg": ["Felt a bit disorganized today.", "Meeting started 20 minutes late.", "Topic wasn't what I expected.", "Too cliquey for my taste.", "Basically just listened to a lecture."]
    },
    "tutoring": {
        "pos": ["The tutor was incredibly helpful with my homework!", "Great session, finally understand the concepts.", "Life-saver before my midterm.", "Learning consultants are the best.", "Super patient and helpful."],
        "neg": ["Too crowded to get one-on-one help.", "Tutor seemed a bit rushed today.", "Wait time was over 30 minutes.", "Didn't really answer my specific question."]
    },
    "testing": {
        "pos": ["Got checked in immediately.", "Surprisingly quiet today.", "Smooth check-in process.", "In and out, no issues."],
        "neg": ["Way too loud for a testing center.", "Line to get in was insane.", "Super stressful environment.", "My keyboard was sticky.", "Too much foot traffic near my station."]
    },
    "east_campus": {
        "pos": ["Love escaping here, so much quieter than city campus.", "Got my Dairy Store ice cream fix.", "Hit up the bowling alley after class.", "Vibes are just better over here.", "Perfect spot for a long study session."],
        "neg": ["Bus ride took forever today.", "Too far from my dorm.", "Kind of dead on the weekends.", "Missed the bus back to city campus."]
    },
    "parking": {
        "pos": ["Found a spot on the first level!", "Actually wasn't full for once.", "Easy in and out today.", "Plenty of open spaces this morning."],
        "neg": ["Took 20 minutes to find a spot.", "People drive like maniacs in here.", "Had to park all the way on the roof.", "Complete gridlock trying to leave.", "Narrow spots, almost got dinged."]
    }
}

# --- LOCAL MOCK DATA (Mirrors your DB) ---
MOCK_COURSES = ["CSCE 155A", "CSCE 156", "MATH 106", "MATH 107", "PHYS 211", "SOFT 160", "ECON 211"]
MOCK_LOCATIONS = [
    {"name": "Love Library", "type": "Study"},
    {"name": "Cather Dining Hall", "type": "Dining"},
    {"name": "DLC Exam Commons", "type": "Testing"},
    {"name": "North 17th Parking Garage", "type": "Parking"},
    {"name": "East Campus", "type": "Zone"},
    {"name": "Avery Hall", "type": "Academic"},
    {"name": "Selleck Building", "type": "Dining"},
    {"name": "14th St Parking Garage", "type": "Parking"}
]
MOCK_ACTIVITIES = [
    {"name": "Coding Club", "type": "club"},
    {"name": "CSCE Resource Center", "type": "tutoring"},
    {"name": "Math Resource Center", "type": "tutoring"},
    {"name": "Aerospace Club", "type": "club"},
    {"name": "NEST Tutoring", "type": "tutoring"},
    {"name": "Astronomy Club", "type": "club"}
]

def generate_csvs():
    users_rows = []
    academics_rows = []
    telemetry_rows = []

    print(f"Generating data for {NUM_USERS} users...")

    for _ in range(NUM_USERS):
        user_id = fake.uuid4()
        # 8-digit NUID
        nuid = str(fake.unique.random_int(min=10000000, max=99999999))

        users_rows.append({
            "user_id": user_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "nuid": nuid
        })

        # Calculate tutoring visits for score-boost correlation
        tutoring_visits = 0
        num_logs = random.randint(6, 12)

        for _ in range(num_logs):
            visit_date = fake.date_time_between(start_date="-30d", end_date="now").strftime("%Y-%m-%d %H:%M")
            is_activity = random.choice([True, False])

            if is_activity:
                target = random.choice(MOCK_ACTIVITIES)
                t_name = target['name']
                t_cat = target['type'] # 'club' or 'tutoring'
                if t_cat == "tutoring": tutoring_visits += 1
            else:
                target = random.choice(MOCK_LOCATIONS)
                t_name = target['name']
                loc_type = target['type']

                # Context-aware category selection
                if "DLC" in t_name: t_cat = "testing"
                elif "East Campus" in t_name: t_cat = "east_campus"
                elif loc_type == "Parking": t_cat = "parking"
                elif loc_type == "Dining": t_cat = "dining"
                else: t_cat = "study"

            # Review Logic
            rating = ""
            review_text = ""
            if random.random() > 0.6: # 40% chance of a review
                rating = random.randint(1, 5)
                # Select from positive or negative bank based on rating
                bank = REVIEWS[t_cat]["pos"] if rating >= 4 else REVIEWS[t_cat]["neg"]
                review_text = random.choice(bank)

            telemetry_rows.append({
                "user_id": user_id,
                "visited": t_name,
                "date": visit_date,
                "rating": rating,
                "review": review_text
            })

        # Generate Academics
        enrolled = random.sample(MOCK_COURSES, k=random.randint(3, 5))
        for course in enrolled:
            # Base score + boost for attending tutoring
            base = random.uniform(62.0, 84.0)
            boost = tutoring_visits * 4.0
            final_score = round(min(base + boost, 100.0), 1)

            academics_rows.append({
                "user_id": user_id,
                "course_id": course,
                "midterm_score": final_score,
                "tutoring_sessions_last_30_days": tutoring_visits
            })

    # Saving CSVs
    print("Saving CSVs...")

    with open('users_mock.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "first_name", "last_name", "nuid"])
        writer.writeheader()
        writer.writerows(users_rows)

    with open('academics_mock.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "course_id", "midterm_score", "tutoring_sessions_last_30_days"])
        writer.writeheader()
        writer.writerows(academics_rows)

    with open('telemetry_mock.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "visited", "date", "rating", "review"])
        writer.writeheader()
        writer.writerows(telemetry_rows)

    print("Success! Check 'users_mock.csv', 'academics_mock.csv', and 'telemetry_mock.csv'.")

if __name__ == "__main__":
    generate_csvs()
