"""
utils/question_bank.py
──────────────────────
Builds a DISTINCT set of questions for every grade/class, across all five
domains (mathematics, grammar, reading, memory, reasoning).

"Each grade has its corresponding work" is implemented here: the assessment
route only ever serves questions whose `grade` matches the student's grade,
and this module guarantees every grade has a complete, age-appropriate set.

Maths and memory items are generated programmatically and scaled by grade,
so they are guaranteed correct and naturally distinct per grade. Grammar,
reading and reasoning items are authored per grade.

`build_question_bank()` returns a flat list of dicts. Each dict has:
    id, domain, grade, type, text, passage(optional), options, correct,
    time(seconds), diff(easy|medium|hard)
"""
from utils.grades import GRADE_VALUES


def _mk(qid, domain, grade, qtype, text, correct, distractors, time, diff, passage=None):
    """Build one question dict, placing the correct answer at a stable,
    non-obvious position derived from the id (so it isn't always first)."""
    options = list(distractors)
    pos = sum(ord(c) for c in qid) % (len(options) + 1)
    options.insert(pos, correct)
    return {
        "id": qid, "domain": domain, "grade": grade, "type": qtype,
        "text": text, "passage": passage, "options": options,
        "correct": correct, "time": time, "diff": diff,
    }


def _int_distractors(correct, deltas=(1, -2, 3, -4, 5, 7, -6, 9)):
    """Three unique, non-negative wrong answers near `correct`."""
    out = []
    for d in deltas:
        v = correct + d
        if v >= 0 and v != correct and str(v) not in out:
            out.append(str(v))
        if len(out) == 3:
            break
    return out


# ── MATHEMATICS (generated, scaled by grade) ──────────────────────────────────
def _math_questions(gi, g):
    q = []
    # Each tuple: (text, correct_int, time, diff)
    if gi == 0:        # Basic 4
        specs = [
            ("What is 34 + 28?", 34 + 28, 45, "easy"),
            ("What is 90 - 47?", 90 - 47, 45, "easy"),
            ("What is 6 x 7?", 6 * 7, 40, "easy"),
            ("Share 24 sweets equally among 4 children. How many does each get?", 24 // 4, 45, "easy"),
            ("What is 100 - 65?", 100 - 65, 40, "easy"),
        ]
    elif gi == 1:      # Basic 5
        specs = [
            ("What is 245 + 138?", 245 + 138, 50, "easy"),
            ("What is 412 - 187?", 412 - 187, 50, "medium"),
            ("What is 13 x 6?", 13 * 6, 45, "medium"),
            ("What is 144 ÷ 12?", 144 // 12, 45, "medium"),
            ("A bag has 30 oranges. You give away one third. How many remain?", 30 - 30 // 3, 55, "medium"),
        ]
    elif gi == 2:      # Basic 6
        specs = [
            ("What is 15% of 200?", 30, 45, "medium"),
            ("What is 248 + 376?", 248 + 376, 50, "easy"),
            ("What is 25 x 14?", 25 * 14, 55, "medium"),
            ("What is 936 ÷ 8?", 936 // 8, 55, "medium"),
            ("A pencil costs 3 cedis. How much do 17 pencils cost?", 3 * 17, 50, "medium"),
        ]
    elif gi == 3:      # JHS 1
        specs = [
            ("Solve for x: x + 9 = 23", 23 - 9, 50, "medium"),
            ("What is 20% of 350?", 70, 50, "medium"),
            ("What is 18 x 15?", 18 * 15, 55, "medium"),
            ("Simplify: 7 x 8 - 19", 7 * 8 - 19, 45, "easy"),
            ("A car travels 60 km in one hour. How far in 3 hours?", 60 * 3, 50, "easy"),
        ]
    elif gi == 4:      # JHS 2
        specs = [
            ("Solve for x: 3x + 4 = 19", (19 - 4) // 3, 60, "hard"),
            ("What is 35% of 240?", 84, 55, "medium"),
            ("The area of a rectangle 12 cm by 9 cm (in cm²)?", 12 * 9, 50, "medium"),
            ("What is 23 x 17?", 23 * 17, 60, "medium"),
            ("Simplify: 144 ÷ 12 + 5 x 3", 144 // 12 + 5 * 3, 55, "medium"),
        ]
    else:              # JHS 3
        specs = [
            ("Solve for x: 5x - 7 = 28", (28 + 7) // 5, 60, "hard"),
            ("What is 2 to the power of 6?", 2 ** 6, 55, "medium"),
            ("What is 45% of 320?", 144, 60, "hard"),
            ("Solve: 2(x + 3) = 20, find x", (20 // 2) - 3, 65, "hard"),
            ("What is 312 ÷ 13 + 96?", 312 // 13 + 96, 55, "medium"),
        ]
    for i, (text, correct, time, diff) in enumerate(specs, 1):
        q.append(_mk(f"m_{g}_{i}", "mathematics", g, "multiple_choice",
                     text, str(correct), _int_distractors(correct), time, diff))
    return q


# ── MEMORY (generated, scaled by grade) ───────────────────────────────────────
_SEQS = {
    0: [7, 3, 9, 1],
    1: [4, 8, 2, 6, 1],
    2: [5, 1, 8, 3, 6],
    3: [2, 9, 4, 7, 1, 5],
    4: [6, 3, 8, 1, 9, 4],
    5: [1, 7, 4, 9, 2, 6, 3],
}
_WORDS = {
    0: ["APPLE", "RIVER", "CLOCK", "STAR"],
    1: ["BOAT", "PENCIL", "WINDOW", "GARDEN", "MUSIC"],
    2: ["TABLE", "MANGO", "CANDLE", "BRIDGE", "FOREST"],
    3: ["MARKET", "SILVER", "ENGINE", "HARVEST", "PLANET", "JOURNEY"],
    4: ["LANTERN", "COMPASS", "GLACIER", "ORCHARD", "VOYAGE", "MELODY"],
    5: ["ANCHOR", "PRISM", "MEADOW", "QUARRY", "TWILIGHT", "SUMMIT", "CANYON"],
}


def _seq_str(seq):
    return ", ".join(str(n) for n in seq)


def _memory_questions(gi, g):
    q = []
    seq = _SEQS[gi]
    words = _WORDS[gi]

    # 1) Recall the exact sequence
    s = _seq_str(seq)
    d1 = _seq_str(seq[1:] + seq[:1])                 # rotate
    d2 = _seq_str(list(reversed(seq)))               # reversed
    swapped = seq[:]
    swapped[0], swapped[1] = swapped[1], swapped[0]
    d3 = _seq_str(swapped)                            # swap first two
    distractors = [x for x in [d1, d2, d3] if x != s][:3]
    q.append(_mk(f"mem_{g}_1", "memory", g, "memory_recall",
                 f"Study this sequence, then choose it exactly: {s}",
                 s, distractors, 30, "easy"))

    # 2) Which number was in a given position
    pos = (gi % len(seq)) + 1
    ordinal = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh"][pos - 1]
    correct = str(seq[pos - 1])
    others = [str(n) for n in seq if str(n) != correct][:3]
    while len(others) < 3:
        others.append(str(max(seq) + len(others) + 1))
    q.append(_mk(f"mem_{g}_2", "memory", g, "memory_recall",
                 f"Remember the sequence {s}. Which number was {ordinal}?",
                 correct, others[:3], 30, "easy"))

    # 3) Word-list recall
    wpos = 2 if gi < 3 else 3
    wordinal = "second" if wpos == 2 else "third"
    wcorrect = words[wpos - 1]
    wothers = [w for w in words if w != wcorrect][:3]
    q.append(_mk(f"mem_{g}_3", "memory", g, "memory_recall",
                 "Study these words: " + ", ".join(words) + f". Which word was {wordinal}?",
                 wcorrect, wothers, 30, "medium"))

    # 4) Reverse the sequence (harder, higher grades only get the hard version)
    rev = _seq_str(list(reversed(seq)))
    rdist = [s, d1, d3]
    rdist = [x for x in rdist if x != rev][:3]
    q.append(_mk(f"mem_{g}_4", "memory", g, "sequence",
                 f"Which option is {s} written in REVERSE order?",
                 rev, rdist, 35, "hard" if gi >= 3 else "medium"))
    return q


# ── GRAMMAR (authored per grade) ──────────────────────────────────────────────
# (grade_index, text, correct, [distractors], time, diff, type)
_GRAMMAR = [
    # Basic 4
    (0, "Choose the correct sentence:", "She doesn't like ice cream.",
     ["She don't like ice cream.", "She doesn't likes ice cream.", "She do not likes ice cream."], 35, "easy", "sentence_correction"),
    (0, "Pick the correct word: The dog ___ in the garden.", "runs",
     ["run", "running", "ran quickly slow"], 30, "easy", "multiple_choice"),
    (0, "Which word is a naming word (noun)?", "school",
     ["quickly", "jump", "happy"], 30, "easy", "multiple_choice"),
    # Basic 5
    (1, "Choose the correctly punctuated sentence:", "It's a beautiful day.",
     ["Its a beautiful day.", "Its' a beautiful day.", "It is' a beautiful day."], 35, "easy", "sentence_correction"),
    (1, "Identify the verb: 'The children played in the park.'", "played",
     ["children", "park", "the"], 35, "easy", "multiple_choice"),
    (1, "Choose the correct word: The team ___ working hard.", "is",
     ["are", "were", "be"], 40, "medium", "multiple_choice"),
    # Basic 6
    (2, "Which sentence contains an adverb?", "She runs quickly.",
     ["The blue car is fast.", "Happy children played.", "He is tall."], 40, "medium", "multiple_choice"),
    (2, "Choose the correct comparative: This book is ___ than that one.", "more interesting",
     ["most interesting", "interestinger", "interestingest"], 40, "medium", "multiple_choice"),
    (2, "Pick the correct plural of 'child':", "children",
     ["childs", "childes", "childrens"], 35, "easy", "multiple_choice"),
    # JHS 1
    (3, "Select correct subject-verb agreement:", "The list of items is on the desk.",
     ["The list of items are on the desk.", "The list of items were on the desk.", "The list of items be on the desk."], 45, "medium", "sentence_correction"),
    (3, "Choose the correct word: She was so tired she could ___ stay awake.", "hardly",
     ["hard", "hardly not", "not hard"], 45, "medium", "multiple_choice"),
    (3, "What is the past tense of 'bring'?", "brought",
     ["bringed", "brang", "broughten"], 35, "easy", "multiple_choice"),
    # JHS 2
    (4, "Which sentence uses the past perfect tense correctly?", "She had eaten before I arrived.",
     ["She has eaten before I arrived.", "She eating before I arrive.", "She was eaten before I arrived."], 50, "hard", "sentence_correction"),
    (4, "Choose the correct word: Neither the teacher nor the students ___ ready.", "were",
     ["was", "is", "be"], 50, "hard", "multiple_choice"),
    (4, "Identify the conjunction: 'I stayed home because it rained.'", "because",
     ["stayed", "home", "rained"], 40, "medium", "multiple_choice"),
    # JHS 3
    (5, "Which sentence is in the passive voice?", "The letter was written by Ama.",
     ["Ama wrote the letter.", "Ama is writing the letter.", "Ama will write the letter."], 50, "hard", "multiple_choice"),
    (5, "What is the plural of 'analysis'?", "analyses",
     ["analysises", "analysis", "analyzis"], 40, "medium", "multiple_choice"),
    (5, "Choose the correct relative pronoun: The man ___ called is my uncle.", "who",
     ["which", "whose", "whom ever"], 45, "hard", "multiple_choice"),
]


def _grammar_questions():
    out = []
    counters = {}
    for gi, text, correct, distractors, time, diff, qtype in _GRAMMAR:
        g = GRADE_VALUES[gi]
        counters[g] = counters.get(g, 0) + 1
        out.append(_mk(f"g_{g}_{counters[g]}", "grammar", g, qtype,
                       text, correct, distractors, time, diff))
    return out


# ── READING (authored per grade) ──────────────────────────────────────────────
# (grade_index, passage, text, correct, [distractors], time, diff)
_READING = [
    (0, "Kofi has a small farm. He grows maize and keeps three goats. Every morning he feeds the goats before he goes to school.",
     "What does Kofi do before school?", "He feeds the goats.",
     ["He sells maize.", "He plays football.", "He sleeps."], 60, "easy"),
    (0, "The sun gives us light and warmth. Plants need sunlight to grow. Without the sun, the world would be dark and cold.",
     "Why do plants need the sun?", "To grow.",
     ["To sleep.", "To stay cold.", "To hide."], 60, "easy"),
    (1, "Ama walked to the market with her mother. They bought tomatoes, onions and fish for the evening soup. The market was busy and full of colour.",
     "What did Ama and her mother buy?", "Tomatoes, onions and fish.",
     ["Books and pens.", "Shoes and bags.", "Rice and sugar only."], 70, "easy"),
    (1, "A spider spins a web to catch insects. The web is sticky so the insects cannot escape. The spider then wraps and eats them.",
     "Why can't insects escape the web?", "Because it is sticky.",
     ["Because it is large.", "Because it is bright.", "Because it is soft."], 70, "medium"),
    (2, "The Amazon rainforest produces a large share of the world's oxygen. It stretches across nine countries and is home to millions of species of plants and animals.",
     "What is the Amazon known for producing?", "Oxygen.",
     ["Gold.", "Plastic.", "Salt."], 80, "medium"),
    (2, "Maria loved the ocean. Her grandmother had been a lighthouse keeper, and Maria often dreamed of continuing that tradition one day.",
     "What can we infer about Maria?", "She has a family link to the sea.",
     ["She fears the water.", "She has never seen the sea.", "She dislikes her grandmother."], 80, "medium"),
    (3, "Photosynthesis is the process by which plants use sunlight, water and carbon dioxide to produce oxygen and sugar. Without it, most life on Earth would not be possible.",
     "What do plants produce during photosynthesis?", "Oxygen and sugar.",
     ["Carbon dioxide and salt.", "Sunlight and water.", "Soil and stone."], 85, "medium"),
    (3, "Recycling reduces waste by turning used materials into new products. It saves energy and protects natural resources, but it works best when people sort their rubbish correctly.",
     "What helps recycling work best?", "Sorting rubbish correctly.",
     ["Burning all waste.", "Burying everything.", "Buying more plastic."], 85, "medium"),
    (4, "Scientists have found that global temperatures have risen by about 1.1°C since pre-industrial times. Although this seems small, even minor changes can affect weather, sea levels and ecosystems.",
     "What is the main point of the passage?", "Small temperature changes can have large effects.",
     ["Temperatures never change.", "Sea levels are falling.", "Ecosystems are unaffected."], 90, "hard"),
    (4, "The printing press, invented by Gutenberg around 1440, allowed books to be made quickly instead of copied by hand. Knowledge spread rapidly, helping bring about major changes in society.",
     "How did the printing press change society?", "It helped knowledge spread widely.",
     ["It made books rarer.", "It slowed learning.", "It ended writing."], 90, "hard"),
    (5, "Many economists argue that education is the strongest driver of long-term development. A skilled population can adopt new technology, raise productivity and adapt to a changing economy.",
     "According to the passage, why is education important for development?", "It helps people adopt technology and raise productivity.",
     ["It reduces the population.", "It removes the need for work.", "It lowers all prices."], 95, "hard"),
    (5, "Although solar power is clean and increasingly cheap, its main drawback is that it cannot generate electricity at night. Engineers are therefore working on better batteries to store daytime energy.",
     "What is the main drawback of solar power mentioned?", "It cannot generate power at night.",
     ["It is very dirty.", "It is always expensive.", "It uses no sunlight."], 95, "hard"),
]


def _reading_questions():
    out = []
    counters = {}
    for gi, passage, text, correct, distractors, time, diff in _READING:
        g = GRADE_VALUES[gi]
        counters[g] = counters.get(g, 0) + 1
        out.append(_mk(f"r_{g}_{counters[g]}", "reading", g, "reading_passage",
                       text, correct, distractors, time, diff, passage=passage))
    return out


# ── REASONING (authored per grade) ────────────────────────────────────────────
# (grade_index, text, correct, [distractors], time, diff, type)
_REASONING = [
    (0, "What comes next: ▲ ■ ● ▲ ■ ● ▲ __", "■", ["▲", "●", "▼"], 30, "easy", "pattern_recognition"),
    (0, "Big is to Small as Tall is to:", "Short", ["Wide", "Long", "High"], 35, "easy", "multiple_choice"),
    (0, "Which one is different: cat, dog, cow, car?", "car", ["cat", "dog", "cow"], 30, "easy", "multiple_choice"),
    (1, "What number comes next: 2, 4, 6, 8, __?", "10", ["9", "11", "12"], 35, "easy", "pattern_recognition"),
    (1, "Book is to Reading as Fork is to:", "Eating", ["Kitchen", "Metal", "Sharp"], 40, "easy", "multiple_choice"),
    (1, "If COLD is to HOT, then DARK is to:", "Light", ["Night", "Black", "Moon"], 40, "easy", "multiple_choice"),
    (2, "What comes next: 3, 6, 12, 24, __?", "48", ["36", "30", "42"], 45, "medium", "pattern_recognition"),
    (2, "Which shape comes next: ○ □ △ ○ □ △ ○ __?", "□", ["○", "△", "◇"], 35, "easy", "pattern_recognition"),
    (2, "Doctor is to Hospital as Teacher is to:", "School", ["Book", "Chalk", "Bus"], 40, "medium", "multiple_choice"),
    (3, "If all Bloops are Razzies and all Razzies are Lazzies, then all Bloops are:", "Lazzies",
     ["Razzies only", "Not Lazzies", "Neither"], 55, "medium", "pattern_recognition"),
    (3, "Find the next number: 1, 4, 9, 16, __?", "25", ["20", "24", "30"], 50, "medium", "pattern_recognition"),
    (3, "Which word does NOT belong: rose, tulip, oak, daisy?", "oak", ["rose", "tulip", "daisy"], 45, "medium", "multiple_choice"),
    (4, "No mammals are cold-blooded. All whales are mammals. Therefore:", "No whales are cold-blooded.",
     ["All whales are cold-blooded.", "Some whales are cold-blooded.", "Whales are not mammals."], 60, "hard", "pattern_recognition"),
    (4, "Next in the series: 2, 6, 12, 20, 30, __?", "42", ["40", "36", "44"], 60, "hard", "pattern_recognition"),
    (4, "If some artists are painters and all painters are creative, which must be true?", "Some artists are creative.",
     ["All artists are painters.", "No artist is creative.", "All creative people are artists."], 60, "hard", "multiple_choice"),
    (5, "If A > B and B > C, which is true?", "A > C", ["C > A", "A = C", "B > A"], 55, "medium", "pattern_recognition"),
    (5, "Next number: 1, 1, 2, 3, 5, 8, __?", "13", ["11", "12", "10"], 60, "hard", "pattern_recognition"),
    (5, "All squares are rectangles. Some rectangles are not squares. Which must be true?", "Some rectangles are squares.",
     ["No square is a rectangle.", "All rectangles are squares.", "No rectangle is a square."], 65, "hard", "multiple_choice"),
]


def _reasoning_questions():
    out = []
    counters = {}
    for gi, text, correct, distractors, time, diff, qtype in _REASONING:
        g = GRADE_VALUES[gi]
        counters[g] = counters.get(g, 0) + 1
        out.append(_mk(f"rs_{g}_{counters[g]}", "reasoning", g, qtype,
                       text, correct, distractors, time, diff))
    return out


def build_question_bank():
    """Return the full, grade-tagged question bank as a list of dicts."""
    bank = []
    for gi, g in enumerate(GRADE_VALUES):
        bank += _math_questions(gi, g)
        bank += _memory_questions(gi, g)
    bank += _grammar_questions()
    bank += _reading_questions()
    bank += _reasoning_questions()
    return bank
