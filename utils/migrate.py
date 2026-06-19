"""
utils/migrate.py
────────────────
Tiny, dependency-free migration helpers so an EXISTING learnai.db keeps working
after the grade/class feature was added. Designed for SQLite (the default).

- ensure_schema()  : adds any newly-introduced columns to existing tables.
- backfill_grades(): fills in grades/classes/questions for older databases so
                     the grade-aware features have data to work with.

A brand-new database created by db.create_all() + seed already has everything;
these functions are no-ops in that case.
"""
from sqlalchemy import inspect, text
from extensions import db
from utils.grades import GRADE_VALUES


def _is_sqlite():
    return db.engine.dialect.name == "sqlite"


def _columns(table):
    insp = inspect(db.engine)
    try:
        return {c["name"] for c in insp.get_columns(table)}
    except Exception:
        return set()


def _add_column(table, column_def_name, ddl):
    if column_def_name not in _columns(table):
        db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {ddl}'))
        db.session.commit()
        print(f"[migrate] added column {table}.{column_def_name}")


def ensure_schema():
    """Add columns introduced by the grade feature to a pre-existing DB."""
    insp = inspect(db.engine)
    tables = set(insp.get_table_names())
    if "users" not in tables:
        return  # fresh DB; create_all + seed will handle it

    # New columns (only added if missing)
    _add_column("users",       "grade", "grade VARCHAR(20)")
    _add_column("questions",   "grade", "grade VARCHAR(20)")
    _add_column("assessments", "grade", "grade VARCHAR(20)")
    # teacher_classes table is created by db.create_all(); nothing to do here.


def backfill_grades():
    """
    Upgrade older data so the grade features work:
      • give gradeless students a grade (spread across classes)
      • give gradeless teachers a default set of classes
      • make sure every grade has a question set
    Safe to run on every startup — it only touches rows that need it.
    """
    from models import User, Question, TeacherClass, Answer
    from utils.question_bank import build_question_bank

    changed = False

    # 1) Students without a grade → spread them across the grades.
    gradeless = User.query.filter(User.role == "student", (User.grade.is_(None)) | (User.grade == "")).all()
    for i, s in enumerate(gradeless):
        s.grade = GRADE_VALUES[i % len(GRADE_VALUES)]
        changed = True
    if gradeless:
        print(f"[migrate] assigned grades to {len(gradeless)} student(s)")

    # 2) Teachers with no class assigned → give them a sensible default set.
    teachers = User.query.filter_by(role="teacher").all()
    for t in teachers:
        if t.teacher_classes.count() == 0:
            for g in ("basic5", "basic6", "jhs1"):
                db.session.add(TeacherClass(teacher_id=t.id, grade=g))
            changed = True
            print(f"[migrate] assigned default classes to teacher {t.email}")

    # 3) Questions: if any lack a grade, rebuild the bank.
    gradeless_q = Question.query.filter((Question.grade.is_(None)) | (Question.grade == "")).count()
    if gradeless_q:
        if Answer.query.count() == 0:
            # No history depends on these — safest to replace with the proper bank.
            Question.query.delete()
            for q in build_question_bank():
                obj = Question(
                    id=q["id"], domain=q["domain"], grade=q["grade"], type=q["type"],
                    text=q["text"], passage=q.get("passage"), correct_answer=q["correct"],
                    time_limit=q["time"], difficulty=q["diff"], is_active=True,
                )
                obj.options = q["options"]
                db.session.add(obj)
            print("[migrate] rebuilt question bank with grade tags")
        else:
            # History exists — don't delete. Spread old questions across grades
            # by domain, then append the generated bank to fill any empty cells.
            old = Question.query.filter((Question.grade.is_(None)) | (Question.grade == "")).all()
            per_domain = {}
            for q in old:
                idx = per_domain.get(q.domain, 0)
                q.grade = GRADE_VALUES[idx % len(GRADE_VALUES)]
                per_domain[q.domain] = idx + 1
            existing_ids = {q.id for q in Question.query.all()}
            for q in build_question_bank():
                if q["id"] in existing_ids:
                    continue
                obj = Question(
                    id=q["id"], domain=q["domain"], grade=q["grade"], type=q["type"],
                    text=q["text"], passage=q.get("passage"), correct_answer=q["correct"],
                    time_limit=q["time"], difficulty=q["diff"], is_active=True,
                )
                obj.options = q["options"]
                db.session.add(obj)
            print("[migrate] tagged legacy questions and added grade-specific sets")
        changed = True

    if changed:
        db.session.commit()
