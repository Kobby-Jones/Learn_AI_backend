"""utils/seed.py — Seeds DB with questions, materials, and demo users on first run."""
import uuid
import bcrypt
from extensions import db
from models import User, Question, LearningMaterial, TeacherClass
from utils.question_bank import build_question_bank


def seed_if_empty():
    if User.query.first():
        return  # already seeded

    print("[seed] Seeding database...")

    # ── Demo users ────────────────────────────────────────────────────────────
    def make_user(name, email, password, role, grade=None):
        return User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            role=role,
            grade=grade,
            is_active=True,
        )

    # Password is "demo" — matches the demo-account buttons on the Login page.
    # Students are spread across the grades so every class has at least one.
    users = [
        make_user("Alex Johnson",      "alex@student.edu",       "demo", "student", "basic5"),
        make_user("Ms. Sarah Williams","swilliams@school.edu",   "demo", "teacher"),
        make_user("Dr. Michael Chen",  "admin@learnai.edu",      "demo", "admin"),
        make_user("Priya Patel",       "priya@student.edu",      "demo", "student", "basic5"),
        make_user("James Osei",        "josei@student.edu",      "demo", "student", "basic6"),
        make_user("Emma Clarke",       "emma@student.edu",       "demo", "student", "basic4"),
        make_user("Luca Ferrari",      "luca@student.edu",       "demo", "student", "jhs1"),
        make_user("Akosua Mensah",     "akosua@student.edu",     "demo", "student", "jhs2"),
        make_user("Yaw Boateng",       "yaw@student.edu",        "demo", "student", "jhs3"),
        make_user("Nana Adjei",        "nana@student.edu",       "demo", "student", "basic6"),
    ]
    for u in users:
        db.session.add(u)
    db.session.flush()  # assign ids before linking teacher classes

    # The demo teacher is assigned three classes: Basic 5, Basic 6 and JHS 1.
    teacher = next(u for u in users if u.email == "swilliams@school.edu")
    for g in ("basic5", "basic6", "jhs1"):
        db.session.add(TeacherClass(teacher_id=teacher.id, grade=g))

    # ── Questions (grade-tagged: each grade gets its own complete set) ────────
    for q in build_question_bank():
        obj = Question(
            id=q["id"],
            domain=q["domain"],
            grade=q["grade"],
            type=q["type"],
            text=q["text"],
            passage=q.get("passage"),
            correct_answer=q["correct"],
            time_limit=q["time"],
            difficulty=q["diff"],
            is_active=True,
        )
        obj.options = q["options"]
        db.session.add(obj)

    # ── Learning materials ─────────────────────────────────────────────────────
    materials_data = [
        {"id":"m1","title":"Reading Comprehension Strategies","description":"Learn powerful strategies to understand and retain what you read.","domain":"reading","diff":"intermediate","format":"video","duration":18,"url":"https://www.khanacademy.org/ela","thumb":"https://picsum.photos/seed/read1/400/225","tags":["comprehension","strategies","inference"],"rating":4.8,"provider":"Khan Academy","target":"reading_comprehension"},
        {"id":"m2","title":"Inference Skills: Reading Between the Lines","description":"Interactive exercises to help you draw conclusions from text.","domain":"reading","diff":"intermediate","format":"interactive","duration":25,"url":"https://www.readworks.org","thumb":"https://picsum.photos/seed/read2/400/225","tags":["inference","critical thinking","reading"],"rating":4.6,"provider":"ReadWorks","target":"reading_comprehension"},
        {"id":"m3","title":"Vocabulary Builder Worksheet Pack","description":"Printable worksheets to expand your vocabulary and improve reading fluency.","domain":"reading","diff":"beginner","format":"worksheet","duration":30,"url":"https://www.education.com","thumb":"https://picsum.photos/seed/read3/400/225","tags":["vocabulary","fluency","reading"],"rating":4.3,"provider":"Education.com","target":"dyslexia_related"},
        {"id":"m4","title":"Logical Reasoning Puzzles","description":"Develop critical thinking through progressively challenging logic puzzles.","domain":"reasoning","diff":"intermediate","format":"interactive","duration":20,"url":"https://www.brainpop.com","thumb":"https://picsum.photos/seed/reason1/400/225","tags":["logic","puzzles","reasoning"],"rating":4.7,"provider":"BrainPOP","target":"reasoning_related"},
        {"id":"m5","title":"Pattern Recognition Mastery","description":"Visual and numerical pattern exercises to strengthen abstract reasoning skills.","domain":"reasoning","diff":"beginner","format":"practice","duration":15,"url":"https://www.ixl.com","thumb":"https://picsum.photos/seed/reason2/400/225","tags":["patterns","visual","abstract"],"rating":4.4,"provider":"IXL Learning","target":"reasoning_related"},
        {"id":"m6","title":"Memory Training Techniques","description":"Science-backed techniques to improve working memory and information retention.","domain":"memory","diff":"beginner","format":"article","duration":10,"url":"https://www.understood.org","thumb":"https://picsum.photos/seed/mem1/400/225","tags":["memory","mnemonics","retention"],"rating":4.2,"provider":"Understood.org","target":"memory_related"},
        {"id":"m7","title":"Number Sense Foundations","description":"Build a solid understanding of numbers, place value, and basic arithmetic.","domain":"mathematics","diff":"beginner","format":"video","duration":20,"url":"https://www.khanacademy.org/math","thumb":"https://picsum.photos/seed/math1/400/225","tags":["numbers","arithmetic","foundations"],"rating":4.9,"provider":"Khan Academy","target":"dyscalculia_related"},
        {"id":"m8","title":"Dyscalculia Support: Visual Maths","description":"Hands-on visual approaches to understanding mathematics using diagrams and models.","domain":"mathematics","diff":"beginner","format":"interactive","duration":25,"url":"https://www.understood.org","thumb":"https://picsum.photos/seed/math2/400/225","tags":["dyscalculia","visual","maths support"],"rating":4.7,"provider":"Understood.org","target":"dyscalculia_related"},
        {"id":"m9","title":"Phonics & Phonological Awareness","description":"Build core reading skills through structured phonics instruction.","domain":"grammar","diff":"beginner","format":"interactive","duration":20,"url":"https://www.starfall.com","thumb":"https://picsum.photos/seed/gram1/400/225","tags":["phonics","dyslexia","reading"],"rating":4.8,"provider":"Starfall","target":"dyslexia_related"},
        {"id":"m10","title":"Grammar Essentials: Sentences & Clauses","description":"Master the fundamentals of English grammar with clear explanations and examples.","domain":"grammar","diff":"intermediate","format":"video","duration":22,"url":"https://www.khanacademy.org/ela","thumb":"https://picsum.photos/seed/gram2/400/225","tags":["grammar","sentences","syntax"],"rating":4.5,"provider":"Khan Academy","target":"language_disorder"},
        {"id":"m11","title":"Working Memory Exercises for Students","description":"Structured exercises designed to strengthen working memory capacity.","domain":"memory","diff":"intermediate","format":"practice","duration":15,"url":"https://www.cogmed.com","thumb":"https://picsum.photos/seed/mem2/400/225","tags":["working memory","exercises","cognition"],"rating":4.3,"provider":"Cogmed","target":"memory_related"},
        {"id":"m12","title":"Critical Thinking: Logic & Deduction","description":"Step-by-step guide to formal and informal logical reasoning.","domain":"reasoning","diff":"advanced","format":"article","duration":30,"url":"https://www.criticalthinking.org","thumb":"https://picsum.photos/seed/reason3/400/225","tags":["logic","deduction","critical thinking"],"rating":4.6,"provider":"Foundation for Critical Thinking","target":"reasoning_related"},
    ]

    for m in materials_data:
        obj = LearningMaterial(
            id=m["id"],
            title=m["title"],
            description=m["description"],
            domain=m["domain"],
            difficulty_level=m["diff"],
            format=m["format"],
            estimated_duration=m["duration"],
            url=m["url"],
            thumbnail_url=m["thumb"],
            rating=m["rating"],
            provider=m["provider"],
            target_difficulty=m["target"],
            is_active=True,
        )
        obj.tags = m["tags"]
        db.session.add(obj)

    db.session.commit()
    print("[seed] Done. Demo accounts: alex@student.edu / swilliams@school.edu / admin@learnai.edu (all password: demo)")
