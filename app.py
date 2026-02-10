"""
================================================================================
    WEB-BASED E-LEARNING SYSTEM - MAIN APPLICATION MODULE
================================================================================

Institution: West Prime Horizon Institute Inc.
Program: Bachelor of Science in Information Technology
Location: Zamboanga Del Sur

Project Title: E-Learning System
Research Course: Methods of Research In Computing

Researchers:
    - JOHN JETHRO P. UBALES
    - EVONIE T. BANO
    - JAMES B. SUMAGANG
    - AIRESLYN O. PASILAN
    - ALEXIS B. SUMALINOG

Adviser: RANDY L. CAÑETE

Date: February 07, 2026
Version: MVP (Minimum Viable Product)

================================================================================
DESCRIPTION:
    This is the main Flask application module for the Web-Based E-Learning
    System. It handles:
    - User authentication and session management
    - User role-based access control (Admin, Teacher, Student)
    - Course and lesson management
    - Assignment submission and grading
    - Quiz creation and assessment
    - Student progress tracking
    - Resource management
    - Administrative functions

TECHNOLOGY STACK:
    - Framework: Flask (Python web framework)
    - Database: SQLite3 with WAL (Write-Ahead Logging)
    - Frontend: HTML5, CSS3, Jinja2 Templates
    - Security: Werkzeug (password hashing, secure filename handling)

================================================================================
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import functools
import json
from io import StringIO
from flask import Response
import services as svc

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'database.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make enumerate available in Jinja2 templates
app.jinja_env.globals['enumerate'] = enumerate


# ============================================================================
# DATABASE MANAGEMENT
# ============================================================================

def get_db():
    """
    Establish a database connection with proper configuration.
    
    Features:
    - 10-second timeout for concurrent access
    - WAL (Write-Ahead Logging) mode for better concurrency
    - Foreign key constraint enforcement
    
    Returns:
        sqlite3.Connection: Database connection object with row factory
    """
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA foreign_keys = ON;')
    except Exception:
        pass
    return conn


def init_db():
    """
    Initialize the database from schema.sql on first run.
    
    Creates all necessary tables for:
    - User management with roles (admin, teacher, student)
    - Course and lesson organization
    - Assignments and submissions
    - Quizzes and attempts
    - Progress tracking
    """
    if not os.path.exists(DB_PATH):
        with get_db() as db:
                schema_path = os.path.join(BASE_DIR, 'schema.sql')
                with open(schema_path, 'r', encoding='utf8') as f:
                    db.executescript(f.read())


init_db()


# ============================================================================
# DATABASE MIGRATION / SCHEMA UPDATES
# ============================================================================

def _ensure_user_columns():
    """
    Lightweight migration: Ensure new columns exist in users table.
    
    Adds columns:
    - school_id: Student/teacher school identifier
    - bio: User biography/profile description
    """
    conn = get_db()
    try:
        cols = [r['name'] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    except Exception:
        conn.close()
        return
    to_add = []
    if 'school_id' not in cols:
        to_add.append("ALTER TABLE users ADD COLUMN school_id TEXT")
    if 'bio' not in cols:
        to_add.append("ALTER TABLE users ADD COLUMN bio TEXT")
    for stmt in to_add:
        try:
            conn.execute(stmt)
        except Exception:
            pass
    if to_add:
        conn.commit()
    conn.close()


_ensure_user_columns()


def _ensure_deleted_users_table():
    """
    Create deleted_users table for audit trail.
    
    Tracks:
    - Deleted user information (stored as JSON snapshot)
    - Admin who performed deletion
    - Deletion timestamp
    """
    conn = get_db()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS deleted_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                snapshot TEXT,
                deleted_by INTEGER,
                deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception:
        pass
    conn.close()


_ensure_deleted_users_table()


def _ensure_deleted_courses_table():
    """
    Create deleted_courses table for audit trail.
    """
    conn = get_db()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS deleted_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title TEXT,
                teacher_id INTEGER,
                snapshot TEXT,
                deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception:
        pass
    conn.close()

_ensure_deleted_courses_table()


def _ensure_courses_code_column():
    """
    Ensure courses table has a code column for class enrollment.
    
    The course code is used by students to join classes without
    needing direct enrollment by the instructor.
    """
    conn = get_db()
    try:
        cols = [r['name'] for r in conn.execute("PRAGMA table_info(courses)").fetchall()]
    except Exception:
        conn.close()
        return
    if 'code' not in cols:
        try:
            conn.execute("ALTER TABLE courses ADD COLUMN code TEXT")
            conn.commit()
        except Exception:
            pass
    conn.close()


_ensure_courses_code_column()


def _ensure_class_members_table():
    """
    Create class_members junction table for student-course enrollment.
    
    Enables:
    - Students to join courses using course code
    - Tracking of enrollment timestamp
    - Prevention of duplicate enrollments
    """
    conn = get_db()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS class_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(course_id, student_id)
            )
        ''')
        conn.commit()
    except Exception:
        pass
    conn.close()


_ensure_class_members_table()


# ============================================================================
# AUTHENTICATION & USER MANAGEMENT
# ============================================================================

def current_user():
    """
    Retrieve the currently logged-in user from session.
    
    Returns:
        sqlite3.Row or None: User record with id, name, email, role, school_id, bio
    """
    uid = session.get('user_id')
    if not uid:
        return None
    db = get_db()
    user = db.execute('SELECT id, name, email, role, school_id, bio FROM users WHERE id = ?', (uid,)).fetchone()
    db.close()
    return user


def role_required(*roles):
    """
    Decorator for role-based access control.
    
    Restricts route access to users with specified roles.
    Redirects unauthorized users to login page.
    
    Args:
        *roles: Variable length argument list of allowed roles (e.g., 'admin', 'teacher', 'student')
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or user['role'] not in roles:
                flash('Access denied')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_user():
    """Inject current_user into all template contexts."""
    return dict(current_user=current_user())


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Root route: redirect authenticated users to dashboard, others to login."""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration Route
    
    Allows new users to create accounts with role selection (student, teacher, admin).
    Features:
    - Email uniqueness validation
    - Password strength requirements (minimum 6 characters)
    - Role selection during registration
    - Auto-login after successful registration
    """
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        role = request.form.get('role','student')
        if role not in ('student','teacher','admin'):
            flash('Invalid role selected')
            return render_template('register.html')
        if not name or not email or not password:
            flash('Please fill all required fields')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return render_template('register.html')
        try:
            uid = svc.create_user(name, email, password, role)
            # verify stored role
            created = svc.get_user_by_id(uid)
            if created and created['role'] != role:
                flash(f'Registered but role stored as {created["role"]}; expected {role}.')
            # auto-login after registration
            session['user_id'] = uid
            flash('Registration successful — welcome!')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Email already registered.')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login Route
    
    Authenticates users by email and password.
    On success, creates session and redirects to dashboard.
    """
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        if not email or not password:
            flash('Enter email and password')
            return render_template('login.html')
        user = svc.get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash('Logged in')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User Logout Route: clears session and redirects to login."""
    session.clear()
    flash('Logged out')
    return redirect(url_for('login'))


# ============================================================================
# DASHBOARD & USER PROFILE ROUTES
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """
    Main Dashboard Route
    
    Displays personalized content based on user role:
    - Students: Courses joined, latest lessons, progress metrics
    - Teachers: All courses, class management, resource sharing
    - Admins: System overview, user management, administrative tools
    
    Features:
    - Course listing (role-based filtering)
    - Progress tracking for students
    - Resource/lesson recommendations
    - Quick access to academic activities
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    # simple listings
    # For students, only show courses they have joined; teachers/admin see all
    if user['role'] == 'student':
        courses = db.execute('SELECT c.* FROM courses c JOIN class_members cm ON cm.course_id = c.id WHERE cm.student_id = ?', (user['id'],)).fetchall()
    else:
        courses = db.execute('SELECT * FROM courses').fetchall()
    lessons = db.execute('SELECT * FROM lessons ORDER BY id DESC LIMIT 10').fetchall()
    progress_data = None
    if user['role'] == 'student':
        completed = db.execute('SELECT COUNT(DISTINCT l.id) as completed FROM lessons l JOIN assignments a ON a.lesson_id = l.id JOIN submissions s ON s.assignment_id = a.id WHERE s.student_id = ?', (user['id'],)).fetchone()
        total_lessons = db.execute('SELECT COUNT(*) as total FROM lessons').fetchone()
        avg_score = db.execute('SELECT AVG(score) as avg FROM attempts WHERE student_id = ?', (user['id'],)).fetchone()
        completed_count = completed['completed'] if completed else 0
        total_count = total_lessons['total'] if total_lessons else 0
        avg = round(avg_score['avg'],2) if avg_score and avg_score['avg'] is not None else None
        pct = int((completed_count / total_count) * 100) if total_count else 0
        deg = pct * 3.6
        progress_data = {'completed': completed_count, 'total': total_count, 'avg': avg, 'pct': pct, 'deg': deg}
    # gather resources for dashboard:
    resources = []
    try:
        if user['role'] == 'student':
            # show resources from teachers of student's courses
            teacher_ids = list({c['teacher_id'] for c in courses})
            if teacher_ids:
                placeholders = ','.join(['?'] * len(teacher_ids))
                resources = db.execute(f"SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id WHERE r.teacher_id IN ({placeholders}) ORDER BY r.created_at DESC LIMIT 6", tuple(teacher_ids)).fetchall()
        elif user['role'] == 'teacher':
            resources = db.execute('SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id WHERE r.teacher_id = ? ORDER BY r.created_at DESC LIMIT 6', (user['id'],)).fetchall()
        else:
            # admin: show latest resources
            resources = db.execute('SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id ORDER BY r.created_at DESC LIMIT 6').fetchall()
    except Exception:
        resources = []
    db.close()
    return render_template('dashboard.html', user=user, courses=courses, lessons=lessons, progress=progress_data, resources=resources)


# ============================================================================
# COURSE MANAGEMENT ROUTES
# ============================================================================

@app.route('/course/create', methods=['GET', 'POST'])
@role_required('teacher')
def create_course():
    """
    Create Course Route
    
    Allows instructors to create new courses.
    Automatically generates unique course code for student self-enrollment.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        user = current_user()
        cid = svc.create_course(title, description, user['id'])
        # fetch the code
        from services import _get_conn
        conn = _get_conn()
        code_row = conn.execute('SELECT code FROM courses WHERE id = ?', (cid,)).fetchone()
        conn.close()
        code = code_row['code'] if code_row else '—'
        flash(f'Class created with code: {code}')
        flash('Course created')
        return redirect(url_for('teacher_classes'))
    return render_template('create_course.html')


@app.route('/teacher/classes')
@role_required('teacher')
def teacher_classes():
    """List all courses created by the logged-in instructor."""
    user = current_user()
    db = get_db()
    classes = svc.get_teacher_classes(user['id'])
    db.close()
    return render_template('teacher_classes.html', classes=classes)


@app.route('/course/<int:course_id>')
def course_page(course_id):
    """Display course details with all lessons and learning materials."""
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    lessons = db.execute('SELECT * FROM lessons WHERE course_id = ?', (course_id,)).fetchall()
    db.close()
    return render_template('course.html', user=user, course=course, lessons=lessons)


@app.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@role_required('teacher')
def edit_course(course_id):
    """Edit course information (title, description)."""
    user = current_user()
    db = get_db()
    c = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    db.close()
    if not c or c['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        svc.update_course(course_id, title, description)
        flash('Course updated')
        return redirect(url_for('teacher_classes'))
    return render_template('edit_course.html', course=c)


@app.route('/course/<int:course_id>/delete', methods=['POST'])
@role_required('teacher', 'admin')
def delete_course_route(course_id):
    """Delete a course and all associated content."""
    user = current_user()
    db = get_db()
    c = db.execute('SELECT teacher_id FROM courses WHERE id = ?', (course_id,)).fetchone()
    db.close()

    if not c:
        flash('Course not found')
        return redirect(request.referrer or url_for('dashboard'))

    if user['role'] != 'admin' and c['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(request.referrer or url_for('dashboard'))

    # Pass the actual teacher_id to satisfy service check
    ok = svc.remove_course(course_id, c['teacher_id'])
    if ok:
        flash('Class deleted')
    else:
        flash('Could not delete class')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/join_class', methods=['GET', 'POST'])
@role_required('student')
def join_class():
    """
    Join Class Route
    
    Allows students to enroll in courses using course code provided by instructor.
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        code = request.form.get('code','').strip()
        if not code:
            flash('Please enter a class code')
            return render_template('join_class.html')
        try:
            course_id = svc.join_class(user['id'], code)
            flash('Successfully joined the class')
            return redirect(url_for('course_page', course_id=course_id))
        except ValueError:
            flash('Class code not found')
            return render_template('join_class.html')
        except Exception:
            flash('Could not join class')
            return render_template('join_class.html')
    return render_template('join_class.html')


@app.route('/teacher/class/<int:course_id>/members')
@role_required('teacher')
def class_members(course_id):
    """View and manage students enrolled in a course."""
    user = current_user()
    # verify ownership
    db = get_db()
    c = db.execute('SELECT teacher_id FROM courses WHERE id = ?', (course_id,)).fetchone()
    db.close()
    if not c or c['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    students = svc.get_class_students(course_id)
    return render_template('class_members.html', students=students, course_id=course_id)


@app.route('/teacher/class/<int:course_id>/remove_member/<int:student_id>', methods=['POST'])
@role_required('teacher')
def remove_member(course_id, student_id):
    """Remove a student from a course."""
    user = current_user()
    db = get_db()
    c = db.execute('SELECT teacher_id FROM courses WHERE id = ?', (course_id,)).fetchone()
    db.close()
    if not c or c['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    ok = svc.remove_member(course_id, student_id)
    if ok:
        flash('Student removed from class')
    else:
        flash('Could not remove student')
    return redirect(url_for('class_members', course_id=course_id))


# ============================================================================
# LESSON MANAGEMENT ROUTES
# ============================================================================

@app.route('/lesson/create/new', methods=['GET'])
@role_required('teacher')
def create_lesson_select():
    """Show teacher's classes so they can choose which class to add a lesson to."""
    user = current_user()
    db = get_db()
    classes = svc.get_teacher_classes(user['id'])
    db.close()
    return render_template('create_lesson_select.html', classes=classes)


@app.route('/lesson/create/<int:course_id>', methods=['GET', 'POST'])
@role_required('teacher')
def create_lesson(course_id):
    """
    Create Lesson Route
    
    Allows instructors to upload lesson content with optional file attachments.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        f = request.files.get('attachment')
        filename = None
        if f and f.filename:
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        svc.create_lesson(course_id, title, content, filename)
        flash('Lesson created')
        return redirect(url_for('course_page', course_id=course_id))
    # load course title for display and compute human-friendly sequential number
    db = get_db()
    course = db.execute('SELECT title, teacher_id FROM courses WHERE id = ?', (course_id,)).fetchone()
    course_title = course['title'] if course else f'Course {course_id}'
    # compute sequential index among teacher's classes when possible
    course_number = None
    try:
        if course and course['teacher_id']:
            rows = db.execute('SELECT id FROM courses WHERE teacher_id = ? ORDER BY id ASC', (course['teacher_id'],)).fetchall()
            # find 1-based index
            ids = [r['id'] for r in rows]
            if course_id in ids:
                course_number = ids.index(course_id) + 1
    except Exception:
        course_number = None
    db.close()
    return render_template('create_lesson.html', course_id=course_id, course_title=course_title, course_number=course_number)


@app.route('/lesson/<int:lesson_id>')
def lesson_page(lesson_id):
    """Display lesson details with all assignments and quizzes."""
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    lesson = db.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    assignments = db.execute('SELECT * FROM assignments WHERE lesson_id = ?', (lesson_id,)).fetchall()
    quizzes = db.execute('SELECT * FROM quizzes WHERE lesson_id = ?', (lesson_id,)).fetchall()
    db.close()
    return render_template('lesson.html', user=user, lesson=lesson, assignments=assignments, quizzes=quizzes)


@app.route('/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@role_required('teacher')
def edit_lesson(lesson_id):
    """Edit lesson content and attachments."""
    db = get_db()
    lesson = db.execute('SELECT l.*, c.teacher_id FROM lessons l JOIN courses c ON l.course_id = c.id WHERE l.id = ?', (lesson_id,)).fetchone()
    db.close()
    user = current_user()
    if not lesson or lesson['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        svc.update_lesson(lesson_id, title, content)
        flash('Lesson updated')
        return redirect(url_for('course_page', course_id=lesson['course_id']))
    return render_template('edit_lesson.html', lesson=lesson)


@app.route('/lesson/<int:lesson_id>/delete', methods=['POST'])
@role_required('teacher')
def delete_lesson_route(lesson_id):
    """Delete a lesson and all associated content."""
    db = get_db()
    lesson = db.execute('SELECT l.*, c.teacher_id FROM lessons l JOIN courses c ON l.course_id = c.id WHERE l.id = ?', (lesson_id,)).fetchone()
    db.close()
    user = current_user()
    if not lesson or lesson['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    svc.delete_lesson(lesson_id)
    flash('Lesson deleted')
    return redirect(url_for('course_page', course_id=lesson['course_id']))


# ============================================================================
# ASSIGNMENT MANAGEMENT ROUTES
# ============================================================================

@app.route('/assignment/create/<int:lesson_id>', methods=['GET', 'POST'])
@role_required('teacher')
def create_assignment(lesson_id):
    """
    Create Assignment Route
    
    Instructors can create assignments with due dates for student submission.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        svc.create_assignment(lesson_id, title, description, due_date)
        flash('Assignment created')
        return redirect(url_for('lesson_page', lesson_id=lesson_id))
    return render_template('create_assignment.html', lesson_id=lesson_id)


@app.route('/assignment/<int:assignment_id>')
def assignment_detail(assignment_id):
    """
    View Assignment Details
    
    - For students: Shows assignment details and their submission
    - For instructors/admins: Shows all student submissions for grading
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    assignment = db.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,)).fetchone()
    submissions = []
    student_submission = None
    if user['role'] in ('teacher', 'admin'):
        submissions = db.execute(
            'SELECT s.*, u.name as student_name FROM submissions s JOIN users u ON s.student_id = u.id WHERE s.assignment_id = ?',
            (assignment_id,)
        ).fetchall()
    else:
        student_submission = db.execute('SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?',
                                        (assignment_id, user['id'])).fetchone()
    db.close()
    return render_template('assignment_detail.html', assignment=assignment, submissions=submissions,
                           student_submission=student_submission)


@app.route('/assignment/<int:assignment_id>/edit', methods=['GET', 'POST'])
@role_required('teacher')
def edit_assignment(assignment_id):
    """Edit assignment details, description, and due date."""
    db = get_db()
    a = db.execute('SELECT a.*, c.teacher_id FROM assignments a JOIN lessons l ON a.lesson_id = l.id JOIN courses c ON l.course_id = c.id WHERE a.id = ?', (assignment_id,)).fetchone()
    db.close()
    user = current_user()
    if not a or a['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        svc.update_assignment(assignment_id, title, description, due_date)
        flash('Assignment updated')
        return redirect(url_for('lesson_page', lesson_id=a['lesson_id']))
    return render_template('edit_assignment.html', assignment=a)


@app.route('/assignment/<int:assignment_id>/delete', methods=['POST'])
@role_required('teacher')
def delete_assignment_route(assignment_id):
    """Delete an assignment and all associated submissions."""
    db = get_db()
    a = db.execute('SELECT a.*, c.teacher_id FROM assignments a JOIN lessons l ON a.lesson_id = l.id JOIN courses c ON l.course_id = c.id WHERE a.id = ?', (assignment_id,)).fetchone()
    db.close()
    user = current_user()
    if not a or a['teacher_id'] != user['id']:
        flash('Access denied')
        return redirect(url_for('teacher_classes'))
    svc.delete_assignment(assignment_id)
    flash('Assignment deleted')
    return redirect(url_for('lesson_page', lesson_id=a['lesson_id']))


@app.route('/assignment/submit/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    """
    Student Assignment Submission Route
    
    Allows students to submit assignments with:
    - File uploads
    - Text submission
    """
    user = current_user()
    if not user or user['role'] != 'student':
        flash('Only students can submit assignments')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        f = request.files.get('file')
        text = request.form.get('text')
        filename = None
        if f and f.filename:
            filename = secure_filename(f.filename)
            dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(dest)
        svc.submit_assignment(assignment_id, user['id'], filename, text)
        flash('Submitted')
        return redirect(url_for('dashboard'))
    return render_template('submit.html', assignment_id=assignment_id)


@app.route('/assignment/<int:assignment_id>/grade/<int:submission_id>', methods=['POST'])
@role_required('teacher', 'admin')
def grade_submission(assignment_id, submission_id):
    """Grade a student's assignment submission with score and feedback."""
    grade = request.form.get('grade')
    feedback = request.form.get('feedback')
    try:
        g = float(grade) if grade not in (None, '') else None
    except Exception:
        g = None
    svc.grade_submission(submission_id, g, feedback)
    flash('Submission graded')
    return redirect(url_for('assignment_detail', assignment_id=assignment_id))


@app.route('/assignment/<int:assignment_id>/export')
@role_required('teacher', 'admin')
def export_submissions(assignment_id):
    """Export all assignment submissions as CSV for analysis."""
    csv = svc.export_submissions_csv(assignment_id)
    return Response(csv, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename=assignment_{assignment_id}_submissions.csv"})


# ============================================================================
# QUIZ & ASSESSMENT ROUTES
# ============================================================================

@app.route('/quiz/create/<int:lesson_id>', methods=['GET', 'POST'])
@role_required('teacher', 'admin')
def create_quiz(lesson_id):
    """
    Create Quiz Route
    
    Instructors can create quizzes with multiple-choice questions.
    Questions are stored as JSON for flexible question management.
    """
    if request.method == 'POST':
        questions_raw = request.form.get('questions')
        # Expect JSON array of {"question":"...","choices":[...],"answer":index}
        try:
            parsed_questions = json.loads(questions_raw)
        except Exception as e:
            flash('Invalid JSON for questions')
            return render_template('create_quiz.html', lesson_id=lesson_id)
        svc.create_quiz(lesson_id, parsed_questions)
        flash('Quiz created')
        return redirect(url_for('lesson_page', lesson_id=lesson_id))
    return render_template('create_quiz.html', lesson_id=lesson_id)


@app.route('/quiz/<int:quiz_id>', methods=['GET'])
def view_quiz(quiz_id):
    """Display quiz questions to student."""
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    # load quiz via services
    from services import _get_conn
    conn = _get_conn()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    conn.close()
    if not quiz:
        flash('Quiz not found')
        return redirect(url_for('dashboard'))
    questions = json.loads(quiz['questions'])
    return render_template('quiz.html', quiz=quiz, questions=questions)


@app.route('/quiz/<int:quiz_id>/attempt', methods=['POST'])
@role_required('student')
def attempt_quiz(quiz_id):
    """
    Student Quiz Submission Route
    
    Records student answers, calculates score, and displays results.
    """
    user = current_user()
    # load quiz
    from services import _get_conn
    conn = _get_conn()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    conn.close()
    if not quiz:
        flash('Quiz not found')
        return redirect(url_for('dashboard'))
    questions = json.loads(quiz['questions'])
    answers = []
    for i, q in enumerate(questions):
        key = f'q_{i}'
        val = request.form.get(key)
        try:
            ans_index = int(val) if val is not None else None
        except:
            ans_index = None
        answers.append(ans_index)
    # evaluate and store via service
    result = svc.evaluate_quiz_attempt(quiz_id, user['id'], answers)
    return render_template('quiz_result.html', score=result['score'], correct=result['correct'], total=result['total'])


# ============================================================================
# RESOURCE MANAGEMENT ROUTES
# ============================================================================

@app.route('/resources/create', methods=['GET', 'POST'])
@role_required('teacher')
def create_resource():
    """
    Create Learning Resource Route
    
    Instructors can share additional learning resources like documents,
    videos, or supplementary materials.
    """
    user = current_user()
    if request.method == 'POST':
        rtype = request.form.get('type')
        title = request.form.get('title')
        content = request.form.get('content')
        f = request.files.get('attachment')
        fname = None
        if f and f.filename:
            fname = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        svc.create_resource(rtype, title, content, user['id'], fname)
        flash('Resource created')
        return redirect(url_for('dashboard'))
    return render_template('teacher_resource_create.html')


@app.route('/resource/<int:resource_id>')
def view_resource(resource_id):
    """View a specific learning resource with inline preview capability."""
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    r = db.execute('SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id WHERE r.id = ?', (resource_id,)).fetchone()
    db.close()
    if not r:
        flash('Resource not found')
        return redirect(url_for('dashboard'))
    # determine extension for inline display
    attachment = r['attachment'] if 'attachment' in r.keys() else None
    ext = None
    if attachment and isinstance(attachment, str) and '.' in attachment:
        ext = attachment.rsplit('.', 1)[-1].lower()
    return render_template('resource_view.html', resource=r, ext=ext)


@app.route('/resources')
def resources_index():
    """
    Resources Listing Route
    
    Shows resources filtered by user role:
    - Students: Resources from their course instructors
    - Instructors: Their own created resources
    - Admins: All system resources
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    resources = []
    try:
        if user['role'] == 'teacher':
            resources = db.execute('SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id WHERE r.teacher_id = ? ORDER BY r.created_at DESC', (user['id'],)).fetchall()
        elif user['role'] == 'student':
            # show resources from student's course teachers
            teacher_ids = list({c['teacher_id'] for c in db.execute('SELECT c.* FROM courses c JOIN class_members cm ON cm.course_id = c.id WHERE cm.student_id = ?', (user['id'],)).fetchall()})
            if teacher_ids:
                placeholders = ','.join(['?'] * len(teacher_ids))
                resources = db.execute(f"SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id WHERE r.teacher_id IN ({placeholders}) ORDER BY r.created_at DESC", tuple(teacher_ids)).fetchall()
        else:
            resources = db.execute('SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id ORDER BY r.created_at DESC').fetchall()
    except Exception:
        resources = []
    db.close()
    return render_template('resources.html', resources=resources)


@app.route('/resource/<int:resource_id>/delete', methods=['POST'])
@role_required('teacher', 'admin')
def delete_resource_route(resource_id):
    """Delete a learning resource (Owner or Admin)."""
    user = current_user()
    db = get_db()
    resource = db.execute('SELECT teacher_id FROM resources WHERE id = ?', (resource_id,)).fetchone()
    db.close()

    if not resource:
        flash('Resource not found.')
        return redirect(request.referrer or url_for('dashboard'))

    # Check ownership or admin role
    if user['role'] != 'admin' and resource['teacher_id'] != user['id']:
        flash('Access denied. You can only delete your own resources.')
        return redirect(request.referrer or url_for('dashboard'))

    try:
        if svc.delete_resource(resource_id):
            flash('Resource deleted successfully.')
        else:
            flash('Could not delete resource. It may have already been removed.')
    except Exception as e:
        flash(f'An error occurred while deleting the resource: {e}')
    return redirect(request.referrer or url_for('resources_index'))

# ============================================================================
# PROGRESS TRACKING ROUTES
# ============================================================================

@app.route('/progress')
def progress():
    """
    Student Progress Tracking Route
    
    Displays comprehensive learning metrics:
    - Completed lessons count
    - Average quiz scores
    - Overall course progress
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    # completed lessons: count of lessons with at least one submission by the student
    completed = db.execute('SELECT COUNT(DISTINCT l.id) as completed FROM lessons l JOIN assignments a ON a.lesson_id = l.id JOIN submissions s ON s.assignment_id = a.id WHERE s.student_id = ?', (user['id'],)).fetchone()
    total_lessons = db.execute('SELECT COUNT(*) as total FROM lessons').fetchone()
    # average quiz score
    avg_score = db.execute('SELECT AVG(score) as avg FROM attempts WHERE student_id = ?', (user['id'],)).fetchone()
    db.close()
    completed_count = completed['completed'] if completed else 0
    total_count = total_lessons['total'] if total_lessons else 0
    avg = round(avg_score['avg'],2) if avg_score and avg_score['avg'] is not None else None
    return render_template('progress.html', completed=completed_count, total=total_count, avg_score=avg)


# ============================================================================
# USER PROFILE ROUTES
# ============================================================================

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """
    User Profile Management Route
    
    Allows users to update their profile information:
    - Name and email
    - School ID
    - Biography
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        school_id = request.form.get('school_id','').strip()
        bio = request.form.get('bio','').strip()
        if not name or not email:
            flash('Name and email are required')
            return render_template('profile.html', user=user)
        try:
            svc.update_user_profile(user['id'], name, email, school_id or None, bio or None)
            # refresh session user info
            flash('Profile updated')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Email already in use')
            return render_template('profile.html', user=user)
    # GET
    return render_template('profile.html', user=user)


# ============================================================================
# ADMINISTRATIVE ROUTES
# ============================================================================

@app.route('/admin')
@role_required('admin')
def admin_panel():
    """
    Administrative Dashboard
    
    Provides administrators with:
    - User management (create, edit, delete)
    - Role assignment
    - System monitoring
    """
    db = get_db()
    users = db.execute('SELECT id, name, email, role, school_id FROM users').fetchall()
    resources = db.execute('SELECT r.*, u.name as teacher_name FROM resources r LEFT JOIN users u ON r.teacher_id = u.id ORDER BY r.created_at DESC').fetchall()
    db.close()
    return render_template('admin.html', users=users, resources=resources)


@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def admin_edit_user(user_id):
    """Edit user information and roles (Admin only)."""
    db = get_db()
    u = db.execute('SELECT id, name, email, role, school_id, bio FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    if not u:
        flash('User not found')
        return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        school_id = request.form.get('school_id','').strip() or None
        bio = request.form.get('bio','').strip() or None
        role = request.form.get('role','student')
        password = request.form.get('password')
        try:
            svc.update_user_profile(user_id, name, email, school_id, bio)
            svc.set_user_role(user_id, role)

            if password:
                if len(password) < 6:
                    flash('Password must be at least 6 characters.')
                    return render_template('admin_edit_user.html', user=u)
                
                password_hash = generate_password_hash(password)
                db = get_db()
                db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
                db.commit()
                db.close()

            flash('User profile updated successfully.')
            return redirect(url_for('admin_panel'))
        except sqlite3.IntegrityError:
            flash('Email already in use')
            return render_template('admin_edit_user.html', user=u)
    return render_template('admin_edit_user.html', user=u)


@app.route('/admin/user/<int:user_id>/set_role/<role>')
@role_required('admin')
def admin_set_role(user_id, role):
    """Set or change user role."""
    if role not in ('student', 'teacher', 'admin'):
        flash('Invalid role')
        return redirect(url_for('admin_panel'))
    db = get_db()
    db.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    db.commit()
    db.close()
    flash('Role updated')
    return redirect(url_for('admin_panel'))


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def admin_delete_user(user_id):
    """Delete a user account (with audit trail)."""
    cur = current_user()
    if cur and cur['id'] == user_id:
        flash('Cannot delete yourself')
        return redirect(url_for('admin_panel'))
    try:
        # perform immediate hard delete (safe) and record snapshot
        ok = svc.purge_user(user_id)
        if ok:
            flash('User deleted')
        else:
            flash('User not found')
    except Exception as e:
        flash(f'Error deleting user: {e}')
    return redirect(url_for('admin_panel'))


@app.route('/admin/resource/<int:resource_id>/delete', methods=['POST'])
@role_required('admin')
def admin_delete_resource(resource_id):
    """Delete a resource (Admin only)."""
    db = get_db()
    r = db.execute('SELECT attachment FROM resources WHERE id = ?', (resource_id,)).fetchone()
    if r:
        if r['attachment']:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], r['attachment']))
            except Exception:
                pass
        db.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
        db.commit()
        flash('Resource deleted')
    else:
        flash('Resource not found')
    db.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/deleted')
@role_required('admin')
def admin_deleted_users():
    """View audit trail of deleted users (for potential restoration)."""
    rows = svc.list_deleted_users()
    return render_template('admin_deleted.html', rows=rows)


@app.route('/admin/deleted/<int:deleted_id>/restore', methods=['POST'])
@role_required('admin')
def admin_restore_user(deleted_id):
    """Restore a previously deleted user account."""
    try:
        ok = svc.restore_user(deleted_id)
        if ok:
            flash('User restored')
        else:
            flash('Deleted record not found')
    except Exception as e:
        flash(f'Could not restore: {e}')
    return redirect(url_for('admin_deleted_users'))


@app.route('/admin/deleted/<int:deleted_id>/remove', methods=['POST'])
@role_required('admin')
def admin_remove_deleted_record(deleted_id):
    """Permanently remove a deleted user audit record."""
    try:
        ok = svc.delete_deleted_record(deleted_id)
        if ok:
            flash('Deleted record removed')
        else:
            flash('Record not found')
    except Exception as e:
        flash(f'Could not remove record: {e}')
    return redirect(url_for('admin_deleted_users'))


@app.route('/admin/deleted_courses')
@role_required('admin')
def admin_deleted_courses():
    """View audit trail of deleted courses."""
    rows = svc.list_deleted_courses()
    return render_template('admin_deleted_courses.html', rows=rows)


@app.route('/admin/deleted_courses/<int:record_id>/remove', methods=['POST'])
@role_required('admin')
def admin_remove_deleted_course_record(record_id):
    """Permanently remove a deleted course audit record."""
    svc.delete_deleted_course_record(record_id)
    flash('Record removed')
    return redirect(url_for('admin_deleted_courses'))


# ============================================================================
# FILE SERVING ROUTES
# ============================================================================

@app.route('/uploads/<path:filename>')
def uploads(filename):
    """Serve uploaded files (lessons, assignments, resources)."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    """
    Application Entry Point
        
    Starts the Flask development server with:
    - Debug mode enabled for development
    - Automatic code reloading on changes   
    - Interactive debugger for troubleshooting
    
    For production deployment:
    - Use a production WSGI server (Gunicorn, uWSGI)
    - Set debug=False
    - Configure appropriate SECRET_KEY
    """
    app.run(debug=True)
