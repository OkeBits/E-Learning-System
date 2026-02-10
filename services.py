"""
================================================================================
    WEB-BASED E-LEARNING SYSTEM - SERVICES MODULE
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
    This module contains business logic and database service functions for:
    - User account management
    - Course and lesson administration
    - Assignment submission and grading
    - Quiz creation and evaluation
    - Progress tracking and reporting
    - Resource management
    - Administrative operations

================================================================================
"""

import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'database.db')


# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

def _get_conn():
    """
    Establish a database connection with optimal concurrency settings.
    
    Configuration:
    - 10-second timeout for concurrent access
    - WAL (Write-Ahead Logging) for better performance
    - Foreign key constraint enforcement
    
    Returns:
        sqlite3.Connection: Database connection with row factory enabled
    """
    # Add a timeout to wait for locks, allow connections from other threads,
    # and enable WAL for better concurrency.
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA foreign_keys = ON;')
    except Exception:
        pass
    return conn


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def create_user(name: str, email: str, password: str, role: str = 'student', school_id: str = None, bio: str = None) -> int:
    """Create a user and return new user id. Raises sqlite3.IntegrityError if email exists."""
    ph = generate_password_hash(password)
    conn = _get_conn()
    cur = conn.execute('INSERT INTO users (name, email, password_hash, role, school_id, bio) VALUES (?, ?, ?, ?, ?, ?)',
                       (name, email, ph, role, school_id, bio))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid


def get_user_by_email(email: str):
    conn = _get_conn()
    u = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return u


def get_user_by_id(user_id: int):
    conn = _get_conn()
    u = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return u


def update_user_profile(user_id: int, name: str, email: str, school_id: str = None, bio: str = None) -> bool:
    conn = _get_conn()
    try:
        conn.execute('UPDATE users SET name = ?, email = ?, school_id = ?, bio = ? WHERE id = ?',
                     (name, email, school_id, bio, user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise
    conn.close()
    return True


def set_user_role(user_id: int, role: str):
    conn = _get_conn()
    conn.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    conn.commit()
    conn.close()


import random
import string


def _generate_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def create_course(title: str, description: str, teacher_id: int, code: str = None) -> int:
    """Create course with a unique code (generated if not provided)."""
    conn = _get_conn()
    if not code:
        # generate until unique
        for _ in range(10):
            code_candidate = _generate_code()
            exists = conn.execute('SELECT id FROM courses WHERE code = ?', (code_candidate,)).fetchone()
            if not exists:
                code = code_candidate
                break
        if not code:
            raise RuntimeError('Failed to generate unique code')
    cur = conn.execute('INSERT INTO courses (title, description, teacher_id, code) VALUES (?, ?, ?, ?)',
                       (title, description, teacher_id, code))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def create_lesson(course_id: int, title: str, content: str, attachment: str = None) -> int:
    conn = _get_conn()
    cur = conn.execute('INSERT INTO lessons (course_id, title, content, attachments) VALUES (?, ?, ?, ?)',
                       (course_id, title, content, attachment))
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid


def join_class(student_id: int, code: str) -> int:
    conn = _get_conn()
    course = conn.execute('SELECT id FROM courses WHERE code = ?', (code.strip().upper(),)).fetchone()
    if not course:
        conn.close()
        raise ValueError('Class code not found')
    course_id = course['id']
    try:
        cur = conn.execute('INSERT INTO class_members (course_id, student_id) VALUES (?, ?)', (course_id, student_id))
        conn.commit()
        mid = cur.lastrowid
    except sqlite3.IntegrityError:
        # already member
        mid = None
    conn.close()
    return course_id


def get_teacher_classes(teacher_id: int):
    conn = _get_conn()
    rows = conn.execute('SELECT * FROM courses WHERE teacher_id = ?', (teacher_id,)).fetchall()
    conn.close()
    return rows


def get_class_students(course_id: int):
    conn = _get_conn()
    rows = conn.execute('SELECT u.id, u.name, u.email, u.school_id, cm.joined_at FROM class_members cm JOIN users u ON cm.student_id = u.id WHERE cm.course_id = ?', (course_id,)).fetchall()
    conn.close()
    return rows


def student_is_member(student_id: int, course_id: int) -> bool:
    conn = _get_conn()
    r = conn.execute('SELECT id FROM class_members WHERE course_id = ? AND student_id = ?', (course_id, student_id)).fetchone()
    conn.close()
    return bool(r)


def remove_course(course_id: int, teacher_id: int) -> bool:
    conn = _get_conn()
    # ensure teacher owns it
    c = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not c or c['teacher_id'] != teacher_id:
        conn.close()
        return False
    
    # Audit trail: Save to deleted_courses before deleting
    try:
        snapshot = dict(c)
        conn.execute('INSERT INTO deleted_courses (course_id, title, teacher_id, snapshot) VALUES (?, ?, ?, ?)',
                     (course_id, c['title'], teacher_id, json.dumps(snapshot)))
    except Exception:
        pass

    conn.execute('DELETE FROM class_members WHERE course_id = ?', (course_id,))
    conn.execute('DELETE FROM assignments WHERE lesson_id IN (SELECT id FROM lessons WHERE course_id = ?)', (course_id,))
    conn.execute('DELETE FROM lessons WHERE course_id = ?', (course_id,))
    conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()
    return True


def remove_member(course_id: int, student_id: int) -> bool:
    """Remove a student from a class. Returns True if a row was deleted."""
    conn = _get_conn()
    cur = conn.execute('DELETE FROM class_members WHERE course_id = ? AND student_id = ?', (course_id, student_id))
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0


def update_course(course_id: int, title: str, description: str) -> bool:
    conn = _get_conn()
    conn.execute('UPDATE courses SET title = ?, description = ? WHERE id = ?', (title, description, course_id))
    conn.commit()
    conn.close()
    return True


def update_lesson(lesson_id: int, title: str, content: str) -> bool:
    conn = _get_conn()
    conn.execute('UPDATE lessons SET title = ?, content = ? WHERE id = ?', (title, content, lesson_id))
    conn.commit()
    conn.close()
    return True


def update_assignment(assignment_id: int, title: str, description: str, due_date: str = None) -> bool:
    conn = _get_conn()
    conn.execute('UPDATE assignments SET title = ?, description = ?, due_date = ? WHERE id = ?', (title, description, due_date, assignment_id))
    conn.commit()
    conn.close()
    return True


def delete_lesson(lesson_id: int) -> bool:
    conn = _get_conn()
    # delete assignments under lesson and lesson
    conn.execute('DELETE FROM assignments WHERE lesson_id = ?', (lesson_id,))
    conn.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    conn.commit()
    conn.close()
    return True


def delete_assignment(assignment_id: int) -> bool:
    conn = _get_conn()
    conn.execute('DELETE FROM submissions WHERE assignment_id = ?', (assignment_id,))
    conn.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
    conn.commit()
    conn.close()
    return True


def delete_user(user_id: int) -> bool:
    """Soft-delete a user: mark inactive and record a snapshot in deleted_users for restore."""
    import json
    conn = _get_conn()
    try:
        u = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not u:
            conn.close()
            return False

        # if already inactive, nothing to do
        if 'is_active' in u.keys() and u['is_active'] == 0:
            conn.close()
            return False

        # mark user inactive (add column if missing handled elsewhere)
        try:
            conn.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        except Exception:
            # if column missing, ignore and proceed to delete fallback
            pass

        snapshot = dict(u)
        # remove sqlite Row-specific items
        for k in list(snapshot.keys()):
            try:
                snapshot[k] = snapshot[k]
            except Exception:
                snapshot[k] = None

        conn.execute('INSERT INTO deleted_users (user_id, snapshot, deleted_by) VALUES (?, ?, ?)',
                     (user_id, json.dumps(snapshot), None))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.rollback()
        conn.close()
        raise


def create_assignment(lesson_id: int, title: str, description: str = None, due_date: str = None) -> int:
    conn = _get_conn()
    cur = conn.execute('INSERT INTO assignments (lesson_id, title, description, due_date) VALUES (?, ?, ?, ?)',
                       (lesson_id, title, description, due_date))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def submit_assignment(assignment_id: int, student_id: int, file_path: str = None, text: str = None) -> int:
    conn = _get_conn()
    cur = conn.execute('INSERT INTO submissions (assignment_id, student_id, file_path, text) VALUES (?, ?, ?, ?)',
                       (assignment_id, student_id, file_path, text))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def grade_submission(submission_id: int, grade: float, feedback: str = None):
    conn = _get_conn()
    conn.execute('UPDATE submissions SET grade = ?, feedback = ? WHERE id = ?', (grade, feedback, submission_id))
    conn.commit()
    conn.close()


def create_quiz(lesson_id: int, questions: list) -> int:
    """Questions should be a list of dicts: {question: str, choices: [..], answer: index}"""
    qjson = json.dumps(questions)
    conn = _get_conn()
    cur = conn.execute('INSERT INTO quizzes (lesson_id, questions) VALUES (?, ?)', (lesson_id, qjson))
    conn.commit()
    qid = cur.lastrowid
    conn.close()
    return qid


def evaluate_quiz_attempt(quiz_id: int, student_id: int, answers: list) -> dict:
    """Store attempt and return {'score':float,'correct':int,'total':int}. Answers is list of selected indices."""
    conn = _get_conn()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if not quiz:
        conn.close()
        raise ValueError('Quiz not found')
    questions = json.loads(quiz['questions'])
    correct = 0
    for i, q in enumerate(questions):
        try:
            if answers[i] == q.get('answer'):
                correct += 1
        except Exception:
            pass
    total = len(questions)
    score = round((correct / total) * 100, 2) if total else 0
    conn.execute('INSERT INTO attempts (quiz_id, student_id, answers, score) VALUES (?, ?, ?, ?)',
                 (quiz_id, student_id, json.dumps(answers), score))
    conn.commit()
    conn.close()
    return {'score': score, 'correct': correct, 'total': total}


def export_submissions_csv(assignment_id: int) -> str:
    conn = _get_conn()
    rows = conn.execute('SELECT s.id, u.name as student_name, s.file_path, s.text, s.submitted_at, s.grade, s.feedback FROM submissions s JOIN users u ON s.student_id = u.id WHERE s.assignment_id = ?', (assignment_id,)).fetchall()
    conn.close()
    out = ['id,student_name,file_path,text,submitted_at,grade,feedback']
    for r in rows:
        vals = [str(r['id']), r['student_name'] or '', r['file_path'] or '', (r['text'] or '').replace('\n', ' ').replace(',', ';'), r['submitted_at'] or '', str(r['grade'] or ''), (r['feedback'] or '').replace(',', ';')]
        out.append(','.join(vals))
    return '\n'.join(out)


def list_deleted_users():
    import json
    conn = _get_conn()
    rows = conn.execute('SELECT id, user_id, snapshot, deleted_at FROM deleted_users ORDER BY deleted_at DESC').fetchall()
    out = []
    for r in rows:
        try:
            snap = json.loads(r['snapshot']) if r['snapshot'] else {}
        except Exception:
            snap = {}
        out.append({'id': r['id'], 'user_id': r['user_id'], 'deleted_at': r['deleted_at'], 'snapshot': snap, 'name': snap.get('name'), 'email': snap.get('email')})
    conn.close()
    return out


def list_deleted_courses():
    conn = _get_conn()
    rows = conn.execute('SELECT d.*, u.name as teacher_name FROM deleted_courses d LEFT JOIN users u ON d.teacher_id = u.id ORDER BY deleted_at DESC').fetchall()
    conn.close()
    return rows


def delete_deleted_course_record(record_id: int):
    conn = _get_conn()
    conn.execute('DELETE FROM deleted_courses WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()


def get_deleted_snapshot(deleted_id: int):
    conn = _get_conn()
    r = conn.execute('SELECT * FROM deleted_users WHERE id = ?', (deleted_id,)).fetchone()
    conn.close()
    return r


def delete_deleted_record(deleted_id: int) -> bool:
    conn = _get_conn()
    try:
        cur = conn.execute('DELETE FROM deleted_users WHERE id = ?', (deleted_id,))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0
    except Exception:
        conn.rollback()
        conn.close()
        raise


def restore_user(deleted_id: int) -> bool:
    import json
    conn = _get_conn()
    try:
        rec = conn.execute('SELECT * FROM deleted_users WHERE id = ?', (deleted_id,)).fetchone()
        if not rec:
            conn.close()
            return False
        snap = json.loads(rec['snapshot'])
        user_id = rec['user_id']
        # If the user row exists, update fields and reactivate
        existing = conn.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
        cols = [r['name'] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if existing:
            if 'is_active' in cols:
                conn.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
            # update name/email/role/school_id/bio if present
            update_parts = []
            params = []
            for key in ('name','email','role','school_id','bio'):
                if key in cols and snap.get(key) is not None:
                    update_parts.append(f"{key} = ?")
                    params.append(snap.get(key))
            if update_parts:
                params.append(user_id)
                conn.execute('UPDATE users SET ' + ', '.join(update_parts) + ' WHERE id = ?', tuple(params))
        else:
            # recreate user row with snapshot values; include id explicitly
            insert_cols = []
            insert_vals = []
            for key in ('id','name','email','password_hash','role','school_id','bio'):
                if key == 'id':
                    insert_cols.append('id')
                    insert_vals.append(user_id)
                else:
                    if key in cols:
                        insert_cols.append(key)
                        insert_vals.append(snap.get(key))
            # set is_active if available
            if 'is_active' in cols:
                insert_cols.append('is_active')
                insert_vals.append(1)
            if insert_cols:
                placeholders = ','.join(['?'] * len(insert_cols))
                conn.execute(f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({placeholders})", tuple(insert_vals))
        conn.execute('DELETE FROM deleted_users WHERE id = ?', (deleted_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.rollback()
        conn.close()
        raise


def _table_exists(conn, name: str) -> bool:
    r = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (name,)).fetchone()
    return bool(r)


def purge_user(user_id: int) -> bool:
    """Hard-delete a user and related records immediately. Records a snapshot in deleted_users before deletion."""
    import json
    conn = _get_conn()
    try:
        u = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not u:
            conn.close()
            return False

        # record snapshot
        snapshot = dict(u)
        conn.execute('INSERT INTO deleted_users (user_id, snapshot, deleted_by) VALUES (?, ?, ?)',
                     (user_id, json.dumps(snapshot), None))

        # check tables and delete related records safely
        if _table_exists(conn, 'class_members'):
            conn.execute('DELETE FROM class_members WHERE student_id = ?', (user_id,))
        if _table_exists(conn, 'submissions'):
            conn.execute('DELETE FROM submissions WHERE student_id = ?', (user_id,))
        if _table_exists(conn, 'attempts'):
            conn.execute('DELETE FROM attempts WHERE student_id = ?', (user_id,))

        # if teacher, delete their courses and related data
        if _table_exists(conn, 'courses'):
            courses = conn.execute('SELECT id FROM courses WHERE teacher_id = ?', (user_id,)).fetchall()
            for c in courses:
                cid = c['id']
                if _table_exists(conn, 'class_members'):
                    conn.execute('DELETE FROM class_members WHERE course_id = ?', (cid,))
                if _table_exists(conn, 'lessons') and _table_exists(conn, 'assignments'):
                    conn.execute('DELETE FROM assignments WHERE lesson_id IN (SELECT id FROM lessons WHERE course_id = ?)', (cid,))
                    conn.execute('DELETE FROM lessons WHERE course_id = ?', (cid,))
                conn.execute('DELETE FROM courses WHERE id = ?', (cid,))

        # finally delete user
        cur = conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0
    except Exception:
        conn.rollback()
        conn.close()
        raise


def create_resource(resource_type: str, title: str, content: str, teacher_id: int, attachment: str = None) -> int:
    """Create a generic resource (material/module/book). Creates table if missing."""
    conn = _get_conn()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            content TEXT,
            teacher_id INTEGER,
            attachment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cur = conn.execute('INSERT INTO resources (type, title, content, teacher_id, attachment) VALUES (?, ?, ?, ?, ?)',
                           (resource_type, title, content, teacher_id, attachment))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid
    except Exception:
        conn.rollback()
        conn.close()
        raise


def get_teacher_resources(teacher_id: int, resource_type: str = None):
    conn = _get_conn()
    if resource_type:
        rows = conn.execute('SELECT * FROM resources WHERE teacher_id = ? AND type = ? ORDER BY created_at DESC', (teacher_id, resource_type)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM resources WHERE teacher_id = ? ORDER BY created_at DESC', (teacher_id,)).fetchall()
    conn.close()
    return rows


def delete_resource(resource_id: int) -> bool:
    """
    Deletes a resource and its associated file from the filesystem.

    Args:
        resource_id (int): The ID of the resource to delete.

    Returns:
        bool: True if deletion was successful, False if resource not found.
    """
    conn = _get_conn()
    try:
        resource = conn.execute('SELECT attachment FROM resources WHERE id = ?', (resource_id,)).fetchone()
        if not resource:
            return False

        cur = conn.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
        conn.commit()

        if cur.rowcount > 0 and resource['attachment']:
            filepath = os.path.join(BASE_DIR, 'uploads', resource['attachment'])
            if os.path.exists(filepath):
                os.remove(filepath)
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
