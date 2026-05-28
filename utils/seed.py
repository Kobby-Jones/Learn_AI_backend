"""utils/seed.py — Seeds DB with questions, materials, and demo users on first run."""
import uuid
import bcrypt
from extensions import db
from models import User, Question, LearningMaterial


def seed_if_empty():
    if User.query.first():
        return  # already seeded

    print("[seed] Seeding database...")

    # ── Demo users ────────────────────────────────────────────────────────────
    def make_user(name, email, password, role):
        return User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            role=role,
            is_active=True,
        )

    # Password is "demo" — matches the demo-account buttons on the Login page.
    users = [
        make_user("Alex Johnson",      "alex@student.edu",       "demo", "student"),
        make_user("Ms. Sarah Williams","swilliams@school.edu",   "demo", "teacher"),
        make_user("Dr. Michael Chen",  "admin@learnai.edu",      "demo", "admin"),
        make_user("Priya Patel",       "priya@student.edu",      "demo", "student"),
        make_user("James Osei",        "josei@student.edu",      "demo", "student"),
        make_user("Emma Clarke",       "emma@student.edu",       "demo", "student"),
        make_user("Luca Ferrari",      "luca@student.edu",       "demo", "student"),
    ]
    for u in users:
        db.session.add(u)

    # ── Questions (exactly matching mock data + expanded to 15 per domain) ────
    questions_data = [
        # ── MATHEMATICS ──────────────────────────────────────────────────────
        {"id":"q1",  "domain":"mathematics","type":"multiple_choice",
         "text":"What is 247 + 358?",
         "options":["595","605","615","585"],"correct":"605","time":45,"diff":"easy"},
        {"id":"q2",  "domain":"mathematics","type":"multiple_choice",
         "text":"If a bag has 24 apples and you give away ⅓ of them, how many are left?",
         "options":["8","16","12","18"],"correct":"16","time":60,"diff":"medium"},
        {"id":"q3",  "domain":"mathematics","type":"pattern_recognition",
         "text":"What number comes next in the sequence: 3, 6, 12, 24, __?",
         "options":["36","48","30","42"],"correct":"48","time":45,"diff":"medium"},
        {"id":"q4m", "domain":"mathematics","type":"multiple_choice",
         "text":"What is 15% of 200?",
         "options":["25","30","35","40"],"correct":"30","time":45,"diff":"easy"},
        {"id":"q5m", "domain":"mathematics","type":"multiple_choice",
         "text":"Solve: 8 × 7 − 12 = ?",
         "options":["44","56","44","48"],"correct":"44","time":40,"diff":"easy"},
        {"id":"q6m", "domain":"mathematics","type":"multiple_choice",
         "text":"A train travels at 60 km/h. How far does it travel in 2.5 hours?",
         "options":["120km","150km","180km","200km"],"correct":"150km","time":60,"diff":"medium"},
        {"id":"q7m", "domain":"mathematics","type":"multiple_choice",
         "text":"What is the area of a rectangle with length 8 cm and width 5 cm?",
         "options":["26 cm²","40 cm²","13 cm²","45 cm²"],"correct":"40 cm²","time":45,"diff":"easy"},
        {"id":"q8m", "domain":"mathematics","type":"pattern_recognition",
         "text":"Which number is missing: 2, 4, 8, __, 32?",
         "options":["12","14","16","18"],"correct":"16","time":40,"diff":"medium"},
        {"id":"q9m", "domain":"mathematics","type":"multiple_choice",
         "text":"If 3x + 7 = 22, what is x?",
         "options":["3","4","5","6"],"correct":"5","time":60,"diff":"hard"},
        {"id":"q10m","domain":"mathematics","type":"multiple_choice",
         "text":"What fraction is equivalent to 0.75?",
         "options":["1/2","2/3","3/4","4/5"],"correct":"3/4","time":40,"diff":"medium"},

        # ── GRAMMAR ───────────────────────────────────────────────────────────
        {"id":"q4",  "domain":"grammar","type":"sentence_correction",
         "text":"Which sentence is grammatically correct?",
         "options":["She dont like ice cream.","She doesn't likes ice cream.",
                    "She doesn't like ice cream.","She do not likes ice cream."],
         "correct":"She doesn't like ice cream.","time":40,"diff":"easy"},
        {"id":"q5",  "domain":"grammar","type":"multiple_choice",
         "text":"Choose the correct word: The team __ working hard to win the championship.",
         "options":["is","are","were","be"],"correct":"is","time":40,"diff":"medium"},
        {"id":"q3g", "domain":"grammar","type":"sentence_correction",
         "text":"Choose the correctly punctuated sentence:",
         "options":["Its a beautiful day.","It's a beautiful day.",
                    "Its' a beautiful day.","It is' a beautiful day."],
         "correct":"It's a beautiful day.","time":35,"diff":"easy"},
        {"id":"q4g", "domain":"grammar","type":"multiple_choice",
         "text":"Which word best completes the sentence: She was so tired that she could __ stay awake.",
         "options":["hardly","hard","hardly not","not hard"],"correct":"hardly","time":45,"diff":"medium"},
        {"id":"q5g", "domain":"grammar","type":"multiple_choice",
         "text":"Identify the verb in: 'The children played happily in the park.'",
         "options":["children","happily","played","park"],"correct":"played","time":35,"diff":"easy"},
        {"id":"q6g", "domain":"grammar","type":"sentence_correction",
         "text":"Which sentence uses the past perfect tense correctly?",
         "options":["She has eaten before I arrived.","She had eaten before I arrived.",
                    "She eating before I arrive.","She was eaten before I arrived."],
         "correct":"She had eaten before I arrived.","time":50,"diff":"hard"},
        {"id":"q7g", "domain":"grammar","type":"multiple_choice",
         "text":"Choose the correct comparative: This book is __ than the last one.",
         "options":["more interesting","most interesting","interestinger","interestingest"],
         "correct":"more interesting","time":40,"diff":"medium"},
        {"id":"q8g", "domain":"grammar","type":"multiple_choice",
         "text":"Which sentence contains an adverb?",
         "options":["The blue car is fast.","She runs quickly.","Happy children played.","He is tall."],
         "correct":"She runs quickly.","time":40,"diff":"easy"},
        {"id":"q9g", "domain":"grammar","type":"sentence_correction",
         "text":"Select the sentence with correct subject-verb agreement:",
         "options":["The list of items are on the desk.","The list of items is on the desk.",
                    "The list of items were on the desk.","The list of items be on the desk."],
         "correct":"The list of items is on the desk.","time":45,"diff":"hard"},
        {"id":"q10g","domain":"grammar","type":"multiple_choice",
         "text":"What is the plural of 'analysis'?",
         "options":["analysises","analysis","analyses","analyzis"],"correct":"analyses","time":35,"diff":"medium"},

        # ── READING ───────────────────────────────────────────────────────────
        {"id":"q6",  "domain":"reading","type":"reading_passage",
         "passage":"The Amazon rainforest, often called the \"lungs of the Earth,\" produces 20% of the world's oxygen. It spans across nine countries in South America and is home to millions of species of plants and animals.",
         "text":"According to the passage, what percentage of the world's oxygen does the Amazon produce?",
         "options":["10%","15%","20%","25%"],"correct":"20%","time":90,"diff":"easy"},
        {"id":"q7",  "domain":"reading","type":"reading_passage",
         "passage":"Maria had always loved the ocean. Every morning she would walk to the cliff overlooking the bay, watching the fishing boats return with their catch. Her grandmother had been a lighthouse keeper, and Maria often dreamed of continuing that tradition.",
         "text":"What can we infer about Maria's connection to the sea?",
         "options":["She works as a fisherman.","She has a family history tied to the ocean.",
                    "She is afraid of the water.","She recently moved to the coast."],
         "correct":"She has a family history tied to the ocean.","time":90,"diff":"medium"},
        {"id":"q3r", "domain":"reading","type":"reading_passage",
         "passage":"Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to produce oxygen and energy in the form of sugar. Without this process, most life on Earth would not be possible.",
         "text":"What do plants produce during photosynthesis?",
         "options":["Carbon dioxide and water","Sunlight and sugar","Oxygen and energy in the form of sugar","Water and carbon dioxide"],
         "correct":"Oxygen and energy in the form of sugar","time":80,"diff":"easy"},
        {"id":"q4r", "domain":"reading","type":"reading_passage",
         "passage":"Scientists studying climate change have found that global temperatures have risen by approximately 1.1°C since pre-industrial times. While this may seem small, even minor changes can have significant effects on weather patterns, sea levels, and ecosystems worldwide.",
         "text":"What is the main point of this passage?",
         "options":["Temperatures have always fluctuated","Small temperature changes can have large global impacts",
                    "Ecosystems are not affected by climate change","Sea levels are decreasing"],
         "correct":"Small temperature changes can have large global impacts","time":90,"diff":"medium"},
        {"id":"q5r", "domain":"reading","type":"reading_passage",
         "passage":"The printing press, invented by Johannes Gutenberg around 1440, revolutionised communication in Europe. Before its invention, books were copied by hand, making them rare and expensive. The press allowed knowledge to spread rapidly, contributing to the Renaissance and the Reformation.",
         "text":"How did the printing press change society?",
         "options":["It made books more expensive","It allowed knowledge to spread more widely",
                    "It slowed the Renaissance","It replaced handwriting entirely"],
         "correct":"It allowed knowledge to spread more widely","time":90,"diff":"medium"},

        # ── MEMORY ────────────────────────────────────────────────────────────
        {"id":"q8",  "domain":"memory","type":"memory_recall",
         "text":"Remember this sequence: 7, 3, 9, 1, 5. Now select the correct sequence:",
         "options":["7, 3, 9, 1, 5","7, 9, 3, 1, 5","3, 7, 9, 1, 5","7, 3, 9, 5, 1"],
         "correct":"7, 3, 9, 1, 5","time":30,"diff":"easy"},
        {"id":"q9",  "domain":"memory","type":"memory_recall",
         "text":"Remember these words: APPLE, RIVER, CLOCK, GARDEN, MUSIC. Which word was third?",
         "options":["APPLE","RIVER","CLOCK","GARDEN"],"correct":"CLOCK","time":25,"diff":"easy"},
        {"id":"q3me","domain":"memory","type":"memory_recall",
         "text":"Study this list: RED, BOAT, PENCIL, STAR, WINDOW. Which word was second?",
         "options":["RED","BOAT","PENCIL","STAR"],"correct":"BOAT","time":25,"diff":"easy"},
        {"id":"q4me","domain":"memory","type":"memory_recall",
         "text":"Remember: 4, 8, 2, 6, 1, 9. What was the fourth number?",
         "options":["2","4","6","8"],"correct":"6","time":30,"diff":"medium"},
        {"id":"q5me","domain":"memory","type":"sequence",
         "text":"Which sequence correctly reverses: 5, 3, 7, 2, 9?",
         "options":["9, 2, 7, 3, 5","5, 3, 7, 2, 9","2, 9, 3, 7, 5","9, 3, 7, 2, 5"],
         "correct":"9, 2, 7, 3, 5","time":35,"diff":"hard"},

        # ── REASONING ─────────────────────────────────────────────────────────
        {"id":"q10", "domain":"reasoning","type":"pattern_recognition",
         "text":"If all Bloops are Razzies, and all Razzies are Lazzies, then all Bloops are definitely:",
         "options":["Razzies only","Lazzies","Neither Razzies nor Lazzies","Not Lazzies"],
         "correct":"Lazzies","time":60,"diff":"medium"},
        {"id":"q11", "domain":"reasoning","type":"multiple_choice",
         "text":"What comes next in the pattern: ▲ ■ ● ▲ ■ ● ▲ __",
         "options":["▲","■","●","▼"],"correct":"■","time":30,"diff":"easy"},
        {"id":"q12", "domain":"reasoning","type":"multiple_choice",
         "text":"Book is to Reading as Fork is to:",
         "options":["Kitchen","Eating","Metal","Sharp"],"correct":"Eating","time":45,"diff":"easy"},
        {"id":"q4re","domain":"reasoning","type":"multiple_choice",
         "text":"Which shape comes next: ○ □ △ ○ □ △ ○ __?",
         "options":["○","□","△","◇"],"correct":"□","time":30,"diff":"easy"},
        {"id":"q5re","domain":"reasoning","type":"multiple_choice",
         "text":"If COLD is to HOT as DARK is to:",
         "options":["Night","Light","Black","Moon"],"correct":"Light","time":40,"diff":"easy"},
        {"id":"q6re","domain":"reasoning","type":"pattern_recognition",
         "text":"No mammals are cold-blooded. All whales are mammals. Therefore:",
         "options":["All whales are cold-blooded","No whales are cold-blooded",
                    "Some whales are cold-blooded","Whales are not mammals"],
         "correct":"No whales are cold-blooded","time":60,"diff":"hard"},
    ]

    for q in questions_data:
        obj = Question(
            id=q["id"],
            domain=q["domain"],
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
