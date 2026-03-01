import os, random, uuid, requests
from datetime import datetime, timedelta, timezone

# ══════════════════════════════════════════════════════════════════
#  CONFIG — edit these two lines
# ══════════════════════════════════════════════════════════════════
HASURA_URL          = os.getenv("HASURA_GRAPHQL_ENDPOINT")
HASURA_ADMIN_SECRET = os.getenv("HASURA_GRAPHQL_ADMIN_SECRET")
# ══════════════════════════════════════════════════════════════════

HEADERS = {
    "Content-Type":          "application/json",
    "x-hasura-admin-secret": HASURA_ADMIN_SECRET,
}
NUM_USERS      = 50
TUTORING_RATIO = 0.40
CHUNK_SIZE     = 50       # rows per mutation batch
random.seed(42)

# ── Name / password pools ─────────────────────────────────────────
FIRST_NAMES = [
    "Aiden","Ava","Benjamin","Charlotte","Caleb","Chloe","Daniel","Emily",
    "Elijah","Emma","Ethan","Grace","Finn","Hannah","Gabriel","Isabella",
    "Henry","Jasmine","Isaac","Julia","Jack","Kayla","James","Lily",
    "Jayden","Madison","Joshua","Maya","Kevin","Mia","Liam","Natalie",
    "Logan","Nora","Lucas","Olivia","Mason","Rachel","Matthew","Riley",
    "Michael","Samantha","Nathan","Sofia","Nicholas","Sophia","Noah","Taylor",
    "Oliver","Victoria",
]
LAST_NAMES = [
    "Anderson","Baker","Carter","Clark","Davis","Edwards","Evans","Foster",
    "Garcia","Green","Hall","Harris","Jackson","Johnson","Jones","Kim",
    "Lee","Lewis","Martin","Martinez","Miller","Mitchell","Moore","Nelson",
    "Parker","Patel","Perez","Phillips","Roberts","Robinson","Rodriguez",
    "Scott","Smith","Taylor","Thomas","Thompson","Turner","Walker","White",
    "Williams","Wilson","Wright","Young","Zhang","Brown","Campbell","Collins",
    "Cooper","Flores","Hughes",
]
WORD_LIST = [
    "apple","bridge","cactus","daisy","eagle","forest","garden","harbor",
    "island","jungle","kettle","lemon","mango","napkin","orange","pepper",
    "quartz","rabbit","salmon","tulip","umbrella","violet","walnut","xenon",
    "yellow","zipper","anchor","butter","candle","dagger","engine","falcon",
    "gravel","honey","igloo","jasper","koala","lantern","marble","nectar",
    "oyster","pine","quill","river","stone","thorn","viper","wheat","yam",
    "zebra","acorn","blaze","cedar","drift","ember","flint","grove","haze",
    "inlet","jade","kelp","lava","marsh","nova","opal","pebble","ridge",
    "slate","tide","vale","wren","frost","gloom","haven",
]
TERMS       = ["Spring 2024","Fall 2024","Spring 2025","Fall 2025"]
STUDY_MODES = ["Solo","Group","Tutoring","Online"]
EXAM_TYPES  = ["Midterm","Final","Quiz"]

# ── Review text pools ─────────────────────────────────────────────
SENTIMENT = {
    "Tutoring": {
        "high": [
            "The NEST tutors were incredibly helpful — my score jumped after just two sessions.",
            "Math Resource Center saved me during finals week. Patient and knowledgeable staff.",
            "I finally understood recursion after one session at the CSCE Resource Center. Go here.",
            "Chemistry Resource Center is underrated. Walked in confused, left actually understanding it.",
            "CAST Study Stop has a great vibe and the tutors genuinely know the material.",
            "Free tutoring that's actually useful — every student should know about this.",
            "Showed up to NEST with zero confidence before my midterm. Left feeling ready.",
            "The Math Resource Center tutors don't just give you answers — they actually teach.",
            "Been coming to the Physics Resource Center weekly. Grade went from a C to a B+.",
            "Honestly surprised how much the tutors know. Better than office hours sometimes.",
        ],
        "low": [
            "Had to wait 40+ minutes during midterm week. They really need more tutors.",
            "The tutor I was paired with seemed just as lost as I was on the homework.",
            "Hours are too limited. Closes at 8pm but I don't get out of class until 7:30.",
            "No walk-in spots available the entire week before finals. Needs a better system.",
            "Tutor was helpful but the space is tiny and loud. Hard to focus.",
        ],
    },
    "Testing": {
        "high": [
            "DLC Exam Commons was quiet and well-organized. No complaints.",
            "Smooth check-in, good lighting, and the chairs were actually comfortable.",
            "Proctors were professional and the room wasn't freezing for once.",
            "Clean, quiet, and efficient. Best testing environment on campus.",
            "Finally a testing room with decent monitors. Made a real difference.",
        ],
        "low": [
            "The AC was blasting so loud I could barely think. Bring a jacket.",
            "Could hear hallway conversations through the wall the whole time.",
            "My computer lagged mid-exam and the proctor took forever to come over.",
            "Chairs are brutal for a 2-hour exam. My back was wrecked by the end.",
            "Sticky keyboard and a skipping mouse. Not ideal test conditions.",
            "Check-in line was backed up 20 minutes before my exam started. Stressful.",
            "Room was overcrowded. People were basically shoulder to shoulder.",
            "The clock on the wall was wrong and nobody fixed it. Panicked for nothing.",
        ],
    },
    "Dining": {
        "high": [
            "East Campus Dairy Store ice cream is an underrated gem. Worth the walk.",
            "Abel dining has the best breakfast on campus, no contest.",
            "Selleck surprised me — way more variety than I expected for a dining hall.",
            "The Dairy Store's cheese curds are incredible. Support UNL's ag program!",
            "Cather dining is always clean and the staff are friendly. Underrated spot.",
            "The made-to-order station at Abel is consistently good. Never disappointed.",
            "Love that they rotate the menu. Actually excited to go eat some nights.",
        ],
        "low": [
            "Lines at Abel between 12–1pm are brutal. Eat before noon or after 1.",
            "Wish there were more vegetarian options available in the evenings.",
            "Food quality really drops toward the end of the semester.",
            "The dining app said they had my favorite dish and it was already gone by noon.",
            "Seating fills up fast during peak hours. Ended up eating standing.",
        ],
    },
    "Dining/General": {
        "high": [
            "Nebraska Union is one of the most convenient spots on campus. Always something open.",
            "Love grabbing lunch at the Union between classes. Fast, easy, decent variety.",
            "The Union food court beats most dining halls for quick grab-and-go options.",
            "Central location makes this the best place to meet up between classes.",
        ],
        "low": [
            "Nebraska Union gets absolutely slammed at noon. Avoid if you have any time pressure.",
            "Prices at the Union have crept up. Feels like off-campus is cheaper now.",
            "Seating fills up fast. You're basically eating standing up by 12:15.",
        ],
    },
    "Parking": {
        "high": [
            "Found a spot in the 14th St garage at 8am with no problem. Early bird wins.",
            "North 17th garage is a bit of a walk but almost always has open spots.",
            "Managed to find street parking right by Kiewit at 9am. Lucky day.",
        ],
        "low": [
            "Parking near Avery Hall is an absolute nightmare. Plan to walk from a garage.",
            "Got a ticket for being 6 minutes over. Enforcement here is ruthless.",
            "Permit prices went up again and there are fewer spots than ever. Classic.",
            "The parking app crashes constantly. Had to run back to feed the meter like it's 2005.",
            "Spent 20 minutes circling and still hiked in from the North 17th garage.",
            "Three open spots on the map were all reserved or coned off. Useless.",
            "Got a ticket while actively loading equipment. No grace period at all.",
        ],
    },
    "Study": {
        "high": [
            "Love Library 3rd floor is my go-to quiet spot. Never too crowded before 10am.",
            "Kiewit Hall has great study rooms and fast Wi-Fi — book them early though.",
            "The collaboration rooms in Avery are perfect for group work.",
            "Found a corner in Hamilton Hall with natural light. Total hidden gem.",
            "Love Library basement is quieter than the floors above. Wish more people knew.",
            "Checked into a Kiewit study room at 7am and had 4 solid hours of focus.",
        ],
        "low": [
            "Love Library fills up completely during finals. Show up early or don't bother.",
            "Some study rooms have zero outlets. Hard to work for any extended session.",
            "Too many people treating the quiet floor like a social area.",
            "Booked a room online and showed up to find someone else already in it.",
            "The Wi-Fi in the basement drops constantly. Ruins any flow you build up.",
        ],
    },
    "Academic": {
        "high": [
            "Well-maintained labs and comfortable classrooms. No complaints.",
            "Professors in this building are consistently available during office hours.",
            "Avery Hall has some of the best computer lab setups on campus.",
            "Clean building, good signage, easy to navigate as a freshman.",
            "Hamilton Hall study nooks on the upper floors are seriously underrated.",
            "Kiewit is brand new and it shows — every room is clean and well-equipped.",
        ],
        "low": [
            "The projector in room 203 has been broken for two weeks. Someone fix it.",
            "Parking nearby is impossible — budget extra time getting to this building.",
            "Heating is completely inconsistent. Wore a coat to class for a week straight.",
            "The elevator is painfully slow. Stairs are faster every single time.",
            "Outlets in the lecture hall are scarce. Get there early if you need to charge.",
        ],
    },
    "Residential": {
        "high": [
            "Abel Hall staff are super responsive. Best RA experience I've had.",
            "The location can't be beat — steps from dining and the quad.",
            "Scott Hall rooms are small but the community vibe makes up for it.",
        ],
        "low": [
            "Laundry machines on my floor are out of order half the time.",
            "Walls are thin and noise carries constantly on weekends. Hard to sleep.",
            "Heating in the room is either freezing or boiling. No middle ground.",
            "Elevators are always broken. Stairs with a mini fridge is not fun.",
        ],
    },
    "Recreation": {
        "high": [
            "Sapp Rec is a great facility. Equipment is modern and well-maintained.",
            "Never too crowded during mid-morning. Love coming here between classes.",
            "The group fitness classes here are actually really good. Free with student ID.",
            "Clean locker rooms and plenty of cardio equipment. No complaints.",
        ],
        "low": [
            "Peak hour wait for the squat racks is insane. Go early or after 7pm.",
            "Locker room could use a deep clean. Not the worst but not great either.",
            "Parking nearby is a nightmare on top of everything else.",
        ],
    },
    "club": {
        "high": [
            "Great club — welcoming community and actually useful for networking.",
            "Been going for a semester and already made solid connections. Glad I joined.",
            "The officers are organized and the meetings are actually worth your time.",
            "Really helped me find my niche on campus. Would recommend to any freshman.",
            "Love the events this club puts on. Genuinely looks good on a resume too.",
            "One of the better-run orgs on campus. Shows up, does what it says it will.",
        ],
        "low": [
            "Meetings run way too long with very little substance. Needs better structure.",
            "Felt a bit cliquey at first. Hard to break in as a new member.",
            "Leadership changes every year and it really shows in the consistency.",
            "Went twice and both times felt like nobody knew what the plan was.",
            "Good concept but the execution is lacking. Potential is there though.",
        ],
    },
    "tutoring": {
        "high": [
            "Honestly one of the most underused resources on campus. The help here is real.",
            "Came in stressed before my exam and left actually confident. That's rare.",
            "The tutors take their time and don't make you feel dumb for asking. 10/10.",
            "Walk-in hours worked perfectly for my schedule. No appointment needed.",
        ],
        "low": [
            "Needed help with a specific topic and the tutor wasn't familiar with it.",
            "Wait times are brutal right before finals. Book ahead or come early.",
            "Room is cramped and it gets loud when multiple sessions are going.",
        ],
    },
    "default": {
        "high": [
            "Great campus resource. Would recommend to other UNL students.",
            "Solid spot. Does exactly what it needs to.",
            "Pleasantly surprised. Will definitely be coming back.",
            "Exactly what I needed. Easy to access and well run.",
        ],
        "low": [
            "Could use some improvement, but it gets the job done.",
            "Not bad, but there's definitely room to do better.",
            "Fine for what it is, but wouldn't go out of my way to come here.",
            "Had higher expectations. Maybe I'll give it another shot.",
        ],
    },
}

def pick_review_text(ltype, rating):
    pool   = SENTIMENT.get(ltype, SENTIMENT["default"])
    bucket = pool["high"] if rating >= 4 else pool["low"]
    return random.choice(bucket)


# ── Core helpers ──────────────────────────────────────────────────
def gql(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(HASURA_URL, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data["data"]

def fetch_all(table, fields, limit=1000):
    """Paginate through a Hasura table to retrieve all rows."""
    rows, offset = [], 0
    while True:
        q     = f"{{ {table}(limit: {limit}, offset: {offset}) {{ {fields} }} }}"
        chunk = gql(q)[table]
        rows += chunk
        if len(chunk) < limit:
            break
        offset += limit
    return rows

def insert_batch(mutation, key, objects, object_type):
    """Insert a list of objects in CHUNK_SIZE batches, print progress."""
    total = len(objects)
    inserted = 0
    for i in range(0, total, CHUNK_SIZE):
        chunk = objects[i:i + CHUNK_SIZE]
        result = gql(mutation, {"objects": chunk})
        inserted += result[key]["affected_rows"]
        print(f"      {inserted}/{total}", end="\r")
    print(f"      {inserted}/{total} ✓")
    return inserted

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def rand_ts(days_back=180):
    dt = datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59))
    return dt.isoformat()

def new_id():
    return str(uuid.uuid4())


# ── Step 1: Fetch reference data ──────────────────────────────────
def fetch_reference_data():
    print("📡 Fetching reference data from Hasura...")
    locations  = fetch_all("locations",  "location_id name type")
    activities = fetch_all("activities", "activity_id name type location_id")
    tags       = fetch_all("tags",       "tag_id")
    courses    = fetch_all("courses",    "course_id name program_id credit_hours")
    programs   = fetch_all("programs",   "program_id name")

    cat     = lambda t: [l for l in locations if l["type"] == t]
    act_cat = lambda t: [a for a in activities if a["type"] == t]

    course_by_program = {}
    for c in courses:
        course_by_program.setdefault(c["program_id"], []).append(c)

    test_locs = cat("Testing") or cat("Academic") or locations

    print(f"   {len(locations)} locations | {len(activities)} activities | "
          f"{len(tags)} tags | {len(courses)} courses | {len(programs)} programs")

    return {
        "locations":         locations,
        "activities":        activities,
        "tags":              tags,
        "courses":           courses,
        "programs":          programs,
        "program_ids":       [p["program_id"] for p in programs],
        "course_by_program": course_by_program,
        "tutoring_locs":     cat("Tutoring"),
        "dining_locs":       cat("Dining"),
        "academic_locs":     cat("Academic"),
        "tutoring_acts":     act_cat("tutoring"),
        "club_acts":         act_cat("club"),
        "test_locs":         test_locs,
        "loc_type_map":      {l["location_id"]: l["type"] for l in locations},
        "act_type_map":      {a["activity_id"]: a["type"] for a in activities},
    }


# ── Step 2: Insert users ──────────────────────────────────────────
def insert_users():
    print("\n👤 Inserting users...")
    ts, used_names, used_nuids, objects = now_iso(), set(), set(), []
    for _ in range(NUM_USERS):
        while True:
            fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            if (fn, ln) not in used_names:
                used_names.add((fn, ln)); break
        while True:
            nuid = f"{random.randint(10000000, 99999999):08d}"
            if nuid not in used_nuids:
                used_nuids.add(nuid); break
        objects.append({
            "user_id":    new_id(),
            "nuid":       nuid,
            "first_name": fn,
            "last_name":  ln,
            "password":   random.choice(WORD_LIST),
            "created_at": ts,
            "updated_at": ts,
        })

    insert_batch("""
        mutation InsertUsers($objects: [users_insert_input!]!) {
            insert_users(objects: $objects) { affected_rows }
        }
    """, "insert_users", objects, "users")
    return objects


# ── Step 3: Declared programs ─────────────────────────────────────
def insert_declared_programs(users, ref):
    print("\n🎓 Inserting declared programs...")
    ts, objects, user_prog = now_iso(), [], {}
    for u in users:
        pid = random.choice(ref["program_ids"])
        user_prog[u["user_id"]] = pid
        objects.append({
            "pos_id":     new_id(),
            "user_id":    u["user_id"],
            "program_id": pid,
            "type":       random.choice(["Major","Minor","Certificate"]),
            "created_at": ts,
            "updated_at": ts,
        })
    insert_batch("""
        mutation InsertPrograms($objects: [declared_programs_insert_input!]!) {
            insert_declared_programs(objects: $objects) { affected_rows }
        }
    """, "insert_declared_programs", objects, "declared_programs")
    return user_prog


# ── Step 4: Enrollment ────────────────────────────────────────────
def insert_enrollment(users, ref, user_prog):
    print("\n📚 Inserting enrollments...")
    ts, objects, user_courses = now_iso(), [], {}
    cbp, all_courses = ref["course_by_program"], ref["courses"]
    for u in users:
        uid, pid = u["user_id"], user_prog[u["user_id"]]
        home   = cbp.get(pid, [])
        others = [c for c in all_courses if c["program_id"] != pid]
        n      = random.randint(3, 5)
        chosen = random.sample(home, min(len(home), n - 1)) if home else []
        chosen += random.sample(others, min(len(others), n - len(chosen)))
        seen, deduped = set(), []
        for c in chosen:
            if c["course_id"] not in seen:
                seen.add(c["course_id"]); deduped.append(c)
        user_courses[uid] = [c["course_id"] for c in deduped]
        for c in deduped:
            objects.append({
                "enroll_id":  new_id(),
                "user_id":    uid,
                "course_id":  c["course_id"],
                "term":       random.choice(TERMS),
                "created_at": ts,
                "updated_at": ts,
            })
    insert_batch("""
        mutation InsertEnrollment($objects: [enrollment_insert_input!]!) {
            insert_enrollment(objects: $objects) { affected_rows }
        }
    """, "insert_enrollment", objects, "enrollment")
    return user_courses


# ── Step 5: User interests ────────────────────────────────────────
def insert_user_interests(users, ref):
    print("\n🏷️  Inserting user interests...")
    ts, objects = now_iso(), []
    for u in users:
        for tag in random.sample(ref["tags"], random.randint(2, 5)):
            objects.append({
                "interest_id": new_id(),
                "user_id":     u["user_id"],
                "tag_id":      tag["tag_id"],
                "created_at":  ts,
                "updated_at":  ts,
            })
    insert_batch("""
        mutation InsertInterests($objects: [user_interests_insert_input!]!) {
            insert_user_interests(objects: $objects) { affected_rows }
        }
    """, "insert_user_interests", objects, "user_interests")


# ── Step 6: Exams + attempts ──────────────────────────────────────
def insert_exams_and_attempts(users, ref, user_courses):
    print("\n📝 Inserting exams...")
    ts        = now_iso()
    test_locs = ref["test_locs"]
    tutored   = set(random.sample(
        [u["user_id"] for u in users], k=int(NUM_USERS * TUTORING_RATIO)
    ))

    # One exam per course
    course_exam, exam_objects = {}, []
    for c in ref["courses"]:
        eid = new_id()
        course_exam[c["course_id"]] = eid
        exam_objects.append({
            "exam_id":     eid,
            "course_id":   c["course_id"],
            "name":        f"{random.choice(EXAM_TYPES)} — {c['name']}",
            "type":        random.choice(EXAM_TYPES),
            "location_id": random.choice(test_locs)["location_id"],
            "created_at":  ts,
            "updated_at":  ts,
        })
    insert_batch("""
        mutation InsertExams($objects: [exams_insert_input!]!) {
            insert_exams(objects: $objects) { affected_rows }
        }
    """, "insert_exams", exam_objects, "exams")

    print("\n📝 Inserting exam attempts...")
    attempt_objects = []
    for u in users:
        uid, is_t = u["user_id"], u["user_id"] in tutored
        for cid in user_courses.get(uid, []):
            eid = course_exam.get(cid)
            if not eid:
                continue
            score     = min(100, random.randint(65, 95) + random.randint(5, 15)) if is_t else random.randint(45, 88)
            pre_mood  = random.randint(1, 5)
            post_mood = min(5, pre_mood + (1 if score >= 75 else 0))
            mode      = "Tutoring" if is_t and random.random() > 0.3 else random.choice(STUDY_MODES)
            attempt_objects.append({
                "attempt_id":  new_id(),
                "exam_id":     eid,
                "user_id":     uid,
                "score":       score,
                "study_mode":  mode,
                "pre_mood":    pre_mood,
                "post_mood":   post_mood,
                "created_at":  rand_ts(),
                "updated_at":  ts,
            })
    insert_batch("""
        mutation InsertAttempts($objects: [exam_attempts_insert_input!]!) {
            insert_exam_attempts(objects: $objects) { affected_rows }
        }
    """, "insert_exam_attempts", attempt_objects, "exam_attempts")

    print(f"   Tutoring-boosted cohort: {len(tutored)}/{NUM_USERS} students")
    return tutored


# ── Step 7: Visits ────────────────────────────────────────────────
def insert_visits(users, ref, tutored):
    print("\n🚶 Inserting visits...")
    tut_acts  = ref["tutoring_acts"]
    club_acts = ref["club_acts"]
    all_acts  = ref["activities"]
    all_locs  = ref["locations"]
    tut_locs  = ref["tutoring_locs"]
    ts, objects = now_iso(), []

    for u in users:
        uid, is_t = u["user_id"], u["user_id"] in tutored
        for _ in range(random.randint(5, 10)):
            r = random.random()
            if is_t and tut_acts and r < 0.55:
                act      = random.choice(tut_acts)
                duration = random.randint(30, 120)
            elif club_acts and r < 0.75:
                act      = random.choice(club_acts)
                duration = random.randint(60, 180)
            else:
                act      = random.choice(all_acts)
                duration = random.randint(15, 90)
            loc_id = act.get("location_id") or \
                     random.choice(tut_locs if is_t and tut_locs else all_locs)["location_id"]
            objects.append({
                "visit_id":         new_id(),
                "user_id":          uid,
                "activity_id":      act["activity_id"],
                "location_id":      loc_id,
                "date":             rand_ts(),
                "duration_minutes": duration,
                "created_at":       ts,
                "updated_at":       ts,
            })
    insert_batch("""
        mutation InsertVisits($objects: [visits_insert_input!]!) {
            insert_visits(objects: $objects) { affected_rows }
        }
    """, "insert_visits", objects, "visits")


# ── Step 8: Reviews ───────────────────────────────────────────────
def insert_reviews(users, ref, tutored):
    print("\n⭐ Inserting reviews...")
    all_locs     = ref["locations"]
    all_acts     = ref["activities"]
    dining_locs  = ref["dining_locs"]
    tut_locs     = ref["tutoring_locs"]
    loc_type_map = ref["loc_type_map"]
    act_type_map = ref["act_type_map"]
    ts, objects  = now_iso(), []

    for u in users:
        uid, is_t = u["user_id"], u["user_id"] in tutored
        for _ in range(random.randint(2, 5)):
            kind = random.choice(["location","activity","course"])
            loc_id = act_id = course_id = None
            ltype  = "default"

            if kind == "location":
                if is_t and tut_locs and random.random() < 0.5:
                    loc = random.choice(tut_locs)
                elif dining_locs and random.random() < 0.35:
                    loc = random.choice(dining_locs)
                else:
                    loc = random.choice(all_locs)
                loc_id = loc["location_id"]
                ltype  = loc.get("type", "default")
            elif kind == "activity":
                act    = random.choice(all_acts)
                act_id = act["activity_id"]
                atype  = act_type_map.get(act_id, "")
                ltype  = atype if atype in SENTIMENT else \
                         loc_type_map.get(act.get("location_id", ""), "default")
            else:
                course_id = random.choice(ref["courses"])["course_id"]

            if is_t and ltype in ("Tutoring","tutoring","Academic"):
                rating = random.choices([3,4,5], weights=[10,35,55])[0]
            elif ltype == "Parking":                   rating = random.choices([1,2,3], weights=[55,30,15])[0]
            elif ltype == "Testing":                   rating = random.choices([2,3,4], weights=[35,40,25])[0]
            elif ltype in ("Dining","Dining/General"): rating = random.choices([3,4,5], weights=[20,45,35])[0]
            elif ltype == "Residential":               rating = random.choices([2,3,4,5], weights=[15,25,35,25])[0]
            elif ltype == "Recreation":                rating = random.choices([3,4,5], weights=[20,40,40])[0]
            elif ltype == "club":                      rating = random.choices([2,3,4,5], weights=[10,20,40,30])[0]
            elif ltype == "tutoring":                  rating = random.choices([3,4,5], weights=[15,35,50])[0]
            else:                                      rating = random.randint(2, 5)

            objects.append({
                "review_id":   new_id(),
                "user_id":     uid,
                "location_id": loc_id,
                "activity_id": act_id,
                "course_id":   course_id,
                "rating":      rating,
                "review_text": pick_review_text(ltype, rating),
                "created_at":  rand_ts(),
                "updated_at":  ts,
            })
    insert_batch("""
        mutation InsertReviews($objects: [reviews_insert_input!]!) {
            insert_reviews(objects: $objects) { affected_rows }
        }
    """, "insert_reviews", objects, "reviews")


# ── Main ──────────────────────────────────────────────────────────
def main():
    print("=" * 56)
    print("  DineU Live Seeder")
    print(f"  Endpoint : {HASURA_URL}")
    print(f"  Users    : {NUM_USERS}  |  Tutoring ratio: {int(TUTORING_RATIO*100)}%")
    print("=" * 56)

    ref          = fetch_reference_data()
    users        = insert_users()
    user_prog    = insert_declared_programs(users, ref)
    user_courses = insert_enrollment(users, ref, user_prog)
    insert_user_interests(users, ref)
    tutored      = insert_exams_and_attempts(users, ref, user_courses)
    insert_visits(users, ref, tutored)
    insert_reviews(users, ref, tutored)

    print("\n" + "=" * 56)
    print("  ✅ Seed complete!")
    print(f"  Tutoring-boosted cohort: {len(tutored)}/{NUM_USERS} students")
    print("=" * 56)


if __name__ == "__main__":
    main()
