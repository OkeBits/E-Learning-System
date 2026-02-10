-- ============================================================================
-- WEB-BASED E-LEARNING SYSTEM - DATABASE SCHEMA
-- ============================================================================
-- 
-- Institution: West Prime Horizon Institute Inc.
-- Program: Bachelor of Science in Information Technology
-- Project: E-Learning System for Senior High School and College Students
-- Adviser: RANDY L. CAÑETE
-- Date: February 07, 2026
--
-- ============================================================================
-- TABLE STRUCTURE
-- ============================================================================

-- USERS: User accounts for administrators, instructors, and students
-- Roles: 'admin', 'teacher', 'student'
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    school_id TEXT,
    bio TEXT
);

-- COURSES: Course/Class information created by instructors
-- The code field is used for student self-enrollment
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    teacher_id INTEGER,
    code TEXT UNIQUE
);

-- LESSONS: Learning materials organized within courses
-- Lessons contain content and optional attachments
CREATE TABLE lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT NOT NULL,
    content TEXT,
    attachments TEXT
);

-- CLASS_MEMBERS: Junction table for student-course enrollment
-- Allows tracking of which students are enrolled in which courses
-- Includes enrollment timestamp for progress tracking
CREATE TABLE class_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, student_id)
);

-- ASSIGNMENTS: Academic tasks assigned to students within lessons
-- Due dates help track assignment completion status
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER,
    title TEXT,
    description TEXT,
    due_date TEXT
);

-- SUBMISSIONS: Student submissions for assignments
-- Tracks both file uploads and text submissions
-- Includes grading information and instructor feedback
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    student_id INTEGER,
    file_path TEXT,
    text TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    grade REAL,
    feedback TEXT
);

-- QUIZZES: Online assessments with JSON-formatted questions
-- Questions stored as JSON array with options and correct answer index
CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER,
    questions TEXT
);

-- ATTEMPTS: Student quiz attempt records for progress tracking
-- Stores answers and calculated scores for assessment analysis
CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    student_id INTEGER,
    answers TEXT,
    score REAL,
    attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RESOURCES TABLE (Optional - for instructor-created learning resources)
-- ============================================================================
-- Stores additional learning materials beyond lessons

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    title TEXT,
    content TEXT,
    attachment TEXT,
    teacher_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

