"""
models/__init__.py  — All SQLAlchemy models, matching frontend TypeScript types exactly.
"""
from extensions import db
from datetime import datetime, timezone
import json

def utcnow():
    return datetime.now(timezone.utc)

# ── User ──────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.String(36), primary_key=True)
    name         = db.Column(db.String(120), nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash= db.Column(db.String(255), nullable=False)
    role         = db.Column(db.String(20), nullable=False, default="student")  # student|teacher|admin
    avatar       = db.Column(db.String(255))
    created_at   = db.Column(db.DateTime, default=utcnow)
    last_login   = db.Column(db.DateTime)
    is_active    = db.Column(db.Boolean, default=True)

    # Preferences stored as JSON string
    _preferences = db.Column("preferences", db.Text,
                              default='{"theme":"light","dyslexiaMode":false,"highContrast":false,'
                                      '"fontSize":"md","reducedMotion":false,"notifications":true}')

    # Relationships
    assessments     = db.relationship("Assessment",    back_populates="student",  lazy="dynamic")
    notifications   = db.relationship("Notification",  back_populates="user",     lazy="dynamic")
    bookmarks       = db.relationship("Bookmark",       back_populates="user",     lazy="dynamic")
    # Teacher → students (many-to-many via enrollment)
    enrolled_students = db.relationship("Enrollment", foreign_keys="Enrollment.teacher_id", back_populates="teacher", lazy="dynamic")
    enrolled_teachers = db.relationship("Enrollment", foreign_keys="Enrollment.student_id", back_populates="student", lazy="dynamic")

    @property
    def preferences(self):
        return json.loads(self._preferences)

    @preferences.setter
    def preferences(self, value):
        self._preferences = json.dumps(value)

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "email":        self.email,
            "role":         self.role,
            "avatar":       self.avatar,
            "createdAt":    self.created_at.isoformat() if self.created_at else None,
            "lastLogin":    self.last_login.isoformat()  if self.last_login  else None,
            "isActive":     self.is_active,
            "preferences":  self.preferences,
        }


# ── Enrollment (teacher → student relationship) ───────────────────────────────
class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id         = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    enrolled_at= db.Column(db.DateTime, default=utcnow)
    teacher    = db.relationship("User", foreign_keys=[teacher_id], back_populates="enrolled_students")
    student    = db.relationship("User", foreign_keys=[student_id], back_populates="enrolled_teachers")


# ── Question ──────────────────────────────────────────────────────────────────
class Question(db.Model):
    __tablename__ = "questions"

    id           = db.Column(db.String(36), primary_key=True)
    domain       = db.Column(db.String(30), nullable=False)  # mathematics|grammar|reading|memory|reasoning
    type         = db.Column(db.String(40), nullable=False)
    text         = db.Column(db.Text, nullable=False)
    passage      = db.Column(db.Text)
    _options     = db.Column("options", db.Text, nullable=False)  # JSON array
    correct_answer = db.Column(db.Text, nullable=False)
    time_limit   = db.Column(db.Integer, default=60)
    difficulty   = db.Column(db.String(10), default="medium")
    image_url    = db.Column(db.String(255))
    is_active    = db.Column(db.Boolean, default=True)

    @property
    def options(self):
        return json.loads(self._options)

    @options.setter
    def options(self, value):
        self._options = json.dumps(value)

    def to_dict(self):
        return {
            "id":            self.id,
            "domain":        self.domain,
            "type":          self.type,
            "text":          self.text,
            "passage":       self.passage,
            "options":       self.options,
            "correctAnswer": self.correct_answer,
            "timeLimit":     self.time_limit,
            "difficulty":    self.difficulty,
            "imageUrl":      self.image_url,
        }


# ── Assessment ────────────────────────────────────────────────────────────────
class Assessment(db.Model):
    __tablename__ = "assessments"

    id           = db.Column(db.String(36), primary_key=True)
    student_id   = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    status       = db.Column(db.String(20), default="pending")  # pending|in_progress|completed|analysing
    started_at   = db.Column(db.DateTime, default=utcnow)
    completed_at = db.Column(db.DateTime)

    student  = db.relationship("User",   back_populates="assessments")
    answers  = db.relationship("Answer", back_populates="assessment", cascade="all, delete-orphan")
    result   = db.relationship("AssessmentResult", back_populates="assessment", uselist=False)

    def to_dict(self):
        return {
            "id":          self.id,
            "studentId":   self.student_id,
            "status":      self.status,
            "startedAt":   self.started_at.isoformat()   if self.started_at   else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
        }


# ── Answer ────────────────────────────────────────────────────────────────────
class Answer(db.Model):
    __tablename__ = "answers"

    id            = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.String(36), db.ForeignKey("assessments.id"), nullable=False)
    question_id   = db.Column(db.String(36), db.ForeignKey("questions.id"),   nullable=False)
    answer        = db.Column(db.Text)
    response_time = db.Column(db.Integer, default=0)  # ms
    is_correct    = db.Column(db.Boolean)
    skipped       = db.Column(db.Boolean, default=False)

    assessment = db.relationship("Assessment", back_populates="answers")
    question   = db.relationship("Question")

    def to_dict(self):
        return {
            "questionId":   self.question_id,
            "answer":       self.answer,
            "responseTime": self.response_time,
            "isCorrect":    self.is_correct,
            "skipped":      self.skipped,
        }


# ── Assessment Result ─────────────────────────────────────────────────────────
class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"

    id                  = db.Column(db.String(36), primary_key=True)
    assessment_id       = db.Column(db.String(36), db.ForeignKey("assessments.id"), unique=True)
    student_id          = db.Column(db.String(36), db.ForeignKey("users.id"))
    completed_at        = db.Column(db.DateTime, default=utcnow)
    overall_score       = db.Column(db.Float, default=0)
    time_spent          = db.Column(db.Integer, default=0)  # seconds

    # Classification
    primary_difficulty  = db.Column(db.String(50))
    confidence_score    = db.Column(db.Float, default=0)
    risk_level          = db.Column(db.String(10))
    strengths           = db.Column(db.Text, default="[]")   # JSON array of domains
    weaknesses          = db.Column(db.Text, default="[]")
    summary             = db.Column(db.Text)
    detailed_analysis   = db.Column(db.Text)
    recommendations     = db.Column(db.Text, default="[]")   # JSON array of strings

    # Domain scores stored as JSON
    _domain_scores      = db.Column("domain_scores", db.Text, default="[]")

    assessment = db.relationship("Assessment", back_populates="result")
    rec_set    = db.relationship("RecommendationSet", back_populates="result", uselist=False)

    @property
    def domain_scores(self):
        return json.loads(self._domain_scores)

    @domain_scores.setter
    def domain_scores(self, value):
        self._domain_scores = json.dumps(value)

    def to_dict(self):
        student = User.query.get(self.student_id)
        return {
            "id":              self.id,
            "assessmentId":    self.assessment_id,
            "studentId":       self.student_id,
            "studentName":     student.name if student else "Unknown",
            "completedAt":     self.completed_at.isoformat() if self.completed_at else None,
            "overallScore":    round(self.overall_score, 1),
            "timeSpent":       self.time_spent,
            "classification": {
                "primaryDifficulty": self.primary_difficulty,
                "confidenceScore":   round(self.confidence_score, 4),
                "riskLevel":         self.risk_level,
                "domainScores":      self.domain_scores,
                "strengths":         json.loads(self.strengths),
                "weaknesses":        json.loads(self.weaknesses),
                "summary":           self.summary,
                "detailedAnalysis":  self.detailed_analysis,
                "recommendations":   json.loads(self.recommendations),
            },
        }


# ── Learning Material ─────────────────────────────────────────────────────────
class LearningMaterial(db.Model):
    __tablename__ = "learning_materials"

    id                  = db.Column(db.String(36), primary_key=True)
    title               = db.Column(db.String(255), nullable=False)
    description         = db.Column(db.Text)
    domain              = db.Column(db.String(30))
    difficulty_level    = db.Column(db.String(20), default="intermediate")
    format              = db.Column(db.String(30))   # video|worksheet|interactive|article|practice|quiz
    estimated_duration  = db.Column(db.Integer, default=15)  # minutes
    url                 = db.Column(db.String(500))
    thumbnail_url       = db.Column(db.String(500))
    _tags               = db.Column("tags", db.Text, default="[]")
    rating              = db.Column(db.Float)
    provider            = db.Column(db.String(100))
    is_active           = db.Column(db.Boolean, default=True)
    # Which difficulty it targets
    target_difficulty   = db.Column(db.String(50))

    @property
    def tags(self):
        return json.loads(self._tags)

    @tags.setter
    def tags(self, value):
        self._tags = json.dumps(value)

    def to_dict(self, recommendation_score=0.8, is_bookmarked=False, progress_percent=0):
        return {
            "id":                  self.id,
            "title":               self.title,
            "description":         self.description,
            "domain":              self.domain,
            "difficultyLevel":     self.difficulty_level,
            "format":              self.format,
            "estimatedDuration":   self.estimated_duration,
            "url":                 self.url,
            "thumbnailUrl":        self.thumbnail_url,
            "tags":                self.tags,
            "recommendationScore": recommendation_score,
            "isBookmarked":        is_bookmarked,
            "progressPercent":     progress_percent,
            "rating":              self.rating,
            "provider":            self.provider,
        }


# ── Recommendation Set ────────────────────────────────────────────────────────
class RecommendationSet(db.Model):
    __tablename__ = "recommendation_sets"

    id                  = db.Column(db.String(36), primary_key=True)
    student_id          = db.Column(db.String(36), db.ForeignKey("users.id"))
    assessment_result_id= db.Column(db.String(36), db.ForeignKey("assessment_results.id"))
    generated_at        = db.Column(db.DateTime, default=utcnow)
    primary_focus       = db.Column(db.String(30))
    _material_ids       = db.Column("material_ids", db.Text, default="[]")  # JSON list of IDs

    result = db.relationship("AssessmentResult", back_populates="rec_set")

    @property
    def material_ids(self):
        return json.loads(self._material_ids)

    @material_ids.setter
    def material_ids(self, value):
        self._material_ids = json.dumps(value)


# ── Bookmark ──────────────────────────────────────────────────────────────────
class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.String(36), db.ForeignKey("users.id"))
    material_id = db.Column(db.String(36), db.ForeignKey("learning_materials.id"))
    created_at  = db.Column(db.DateTime, default=utcnow)
    user        = db.relationship("User",            back_populates="bookmarks")
    material    = db.relationship("LearningMaterial")


# ── MaterialProgress ──────────────────────────────────────────────────────────
class MaterialProgress(db.Model):
    __tablename__ = "material_progress"
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.String(36), db.ForeignKey("users.id"))
    material_id   = db.Column(db.String(36), db.ForeignKey("learning_materials.id"))
    progress_pct  = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=utcnow)


# ── Notification ──────────────────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = "notifications"

    id         = db.Column(db.String(36), primary_key=True)
    user_id    = db.Column(db.String(36), db.ForeignKey("users.id"))
    title      = db.Column(db.String(255))
    message    = db.Column(db.Text)
    type       = db.Column(db.String(20), default="info")  # info|success|warning|error
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    link       = db.Column(db.String(255))

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id":        self.id,
            "title":     self.title,
            "message":   self.message,
            "type":      self.type,
            "isRead":    self.is_read,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "link":      self.link,
        }


# ── Audit Log ─────────────────────────────────────────────────────────────────
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    user_name  = db.Column(db.String(120))        # denormalised for display
    action     = db.Column(db.String(80))         # 'User login', 'Assessment completed', etc.
    level      = db.Column(db.String(20), default="info")   # info|success|warning|error
    ip_address = db.Column(db.String(45))
    detail     = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id":      self.id,
            "userId":  self.user_id,
            "user":    self.user_name or "System",
            "action":  self.action,
            "level":   self.level,
            "ip":      self.ip_address or "—",
            "detail":  self.detail,
            "time":    self.created_at.isoformat() if self.created_at else None,
        }


def log_event(user, action: str, level: str = "info", ip: str = None, detail: str = None):
    """Helper to record an audit-log entry. Safe to call anywhere a session is open."""
    entry = AuditLog(
        user_id=user.id if user else None,
        user_name=user.name if user else "System",
        action=action,
        level=level,
        ip_address=ip,
        detail=detail,
    )
    db.session.add(entry)
    return entry
