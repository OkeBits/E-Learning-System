# Web-Based E-Learning System - Code Structure Documentation

## Project Information

**Institution:** West Prime Horizon Institute Inc.  
**Program:** Bachelor of Science in Information Technology  
**Location:** Zamboanga Del Sur  
**Project:** E-Learning System for Senior High School and College Students  
**Adviser:** RANDY L. CAÑETE  
**Date:** February 07, 2026  
**Version:** MVP (Minimum Viable Product)

**Researchers:**
- JOHN JETHRO P. UBALES
- EVONIE T. BANO
- JAMES B. SUMAGANG
- AIRESLYN O. PASSILAN
- ALEXIS B. SUMALINOG

---

## Code Files Overview

### 1. **app.py** - Main Application Module
**Purpose:** Flask application with all route handlers and business logic.

**Key Sections:**
- **Database Management:** Connection pooling, initialization, schema migrations
- **Authentication & Authorization:** User login, registration, role-based access control
- **Dashboard Routes:** Role-specific dashboard displays
- **Course Management:** Create, edit, delete courses; manage enrollment
- **Lesson Management:** Upload lessons, organize content, manage attachments
- **Assignment Management:** Create assignments, handle submissions, grading
- **Quiz & Assessment:** Create quizzes, record attempts, calculate scores
- **Resource Management:** Share learning materials, resources
- **Progress Tracking:** Monitor student learning metrics
- **User Profile:** Profile management and settings
- **Administrative Functions:** User management, audit trails, role assignment
- **File Serving:** Serve uploaded files securely

**Key Functions:**
- `get_db()` - Database connection with WAL mode
- `init_db()` - Initialize database from schema
- `current_user()` - Get logged-in user from session
- `role_required(*roles)` - Decorator for access control

---

### 2. **services.py** - Business Logic Layer
**Purpose:** Database service functions and business operations.

**Key Sections:**
- **Database Connection:** Connection management with optimal concurrency
- **User Management:** Create/update/delete users, password hashing
- **Course Services:** Course creation, enrollment, management
- **Lesson Services:** Lesson CRUD operations
- **Assignment Services:** Assignment handling, submission tracking
- **Quiz Services:** Quiz evaluation, attempt recording
- **Progress Tracking:** Calculate student metrics
- **Resource Services:** Resource creation and management
- **Administrative Services:** User audit trails, role management

**Key Functions:**
- `create_user()` - Register new user
- `get_user_by_email()` / `get_user_by_id()` - User queries
- `create_course()` - Create new course with unique code
- `join_class()` - Student enrollment via course code
- `submit_assignment()` - Record student submission
- `evaluate_quiz_attempt()` - Auto-grade quiz
- `export_submissions_csv()` - Generate reports

---

### 3. **schema.sql** - Database Schema
**Purpose:** Database table definitions and relationships.

**Tables:**
- **users** - User accounts with roles (admin, teacher, student)
- **courses** - Course/class information with enrollment codes
- **lessons** - Learning materials organized by course
- **class_members** - Student-course enrollment junction table
- **assignments** - Assignment definitions within lessons
- **submissions** - Student assignment submissions with grades
- **quizzes** - Quiz definitions with JSON question storage
- **attempts** - Quiz attempt records with scores
- **resources** - Supplementary learning materials

---

### 4. **checks.py** - System Validation
**Purpose:** Pre-startup system integrity checks.

**Checks:**
- Required project files exist (app.py, schema.sql, templates, static)
- Python code compiles without errors
- System ready for deployment

---

## Database Architecture

### Key Design Decisions

1. **WAL Mode (Write-Ahead Logging)**
   - Enables better concurrency for multiple simultaneous users
   - Improves performance over standard SQLite mode

2. **Foreign Key Constraints**
   - Enforced for data integrity
   - Ensures orphaned records cannot exist

3. **JSON Storage for Questions**
   - Flexible quiz question format
   - Supports rich question structures

4. **Audit Trail**
   - Deleted user records stored for recovery
   - Tracks who performed deletion and when

5. **Unique Course Codes**
   - Auto-generated for student self-enrollment
   - Prevents duplicate enrollment attempts

---

## Authentication & Access Control

### User Roles

- **Admin:** Full system access, user management, monitoring
- **Teacher/Instructor:** Course creation, lesson management, grading
- **Student:** Course access, assignment submission, progress tracking

### Role-Based Routes

All protected routes use `@role_required` decorator:
```python
@app.route('/admin')
@role_required('admin')
def admin_panel():
    # Only admins can access
```

---

## Route Organization

### Authentication Routes
- `/` - Root redirect
- `/register` - User registration
- `/login` - User login
- `/logout` - Session termination

### Dashboard & Profile
- `/dashboard` - Main user dashboard (role-based)
- `/profile` - User profile management
- `/progress` - Student progress tracking

### Course Management
- `/course/create` - Create new course (teachers)
- `/course/<id>` - View course details
- `/course/<id>/edit` - Edit course (teacher only)
- `/course/<id>/delete` - Delete course (teacher only)
- `/join_class` - Student course enrollment
- `/teacher/classes` - Teacher's course list
- `/teacher/class/<id>/members` - Manage class students

### Lesson Management
- `/lesson/create/<course_id>` - Create lesson
- `/lesson/<id>` - View lesson details
- `/lesson/<id>/edit` - Edit lesson
- `/lesson/<id>/delete` - Delete lesson

### Assignment Management
- `/assignment/create/<lesson_id>` - Create assignment
- `/assignment/<id>` - View assignment details
- `/assignment/<id>/edit` - Edit assignment
- `/assignment/<id>/delete` - Delete assignment
- `/assignment/submit/<id>` - Student submission
- `/assignment/<id>/grade/<submission_id>` - Grade submission
- `/assignment/<id>/export` - Export submissions as CSV

### Quiz Routes
- `/quiz/create/<lesson_id>` - Create quiz
- `/quiz/<id>` - View quiz questions
- `/quiz/<id>/attempt` - Submit quiz answers

### Resource Routes
- `/resources/create` - Create resource
- `/resource/<id>` - View resource
- `/resources` - List resources

### Administrative Routes
- `/admin` - Admin dashboard
- `/admin/user/<id>/edit` - Edit user
- `/admin/user/<id>/set_role/<role>` - Change user role
- `/admin/user/<id>/delete` - Delete user
- `/admin/deleted` - View deleted users
- `/admin/deleted/<id>/restore` - Restore user

### File Routes
- `/uploads/<filename>` - Serve uploaded files

---

## Key Features Implementation

### 1. User Management
- Secure password hashing with Werkzeug
- Email uniqueness validation
- Role-based access control
- User audit trails for deletions

### 2. Course Enrollment
- Unique course codes for self-enrollment
- Teacher-managed student enrollment
- Track enrollment timestamps

### 3. Content Management
- Lessons with attachments
- Assignment specifications with due dates
- Quiz creation with JSON storage
- Resource sharing by instructors

### 4. Student Submissions
- File upload support
- Text-based submissions
- Automatic timestamp recording

### 5. Grading System
- Manual grading by instructors
- Feedback and score storage
- CSV export for analysis

### 6. Quiz Assessment
- Automatic scoring
- Question review
- Attempt tracking

### 7. Progress Tracking
- Completed lessons count
- Assignment submission tracking
- Average quiz scores
- Visual progress indicators

---

## File Upload Security

- Uses `secure_filename()` from Werkzeug
- Files stored in isolated `uploads/` directory
- Prevents path traversal attacks
- Supports download via `/uploads/<filename>` route

---

## Database Concurrency

**Configuration:**
- 10-second timeout for concurrent access
- WAL (Write-Ahead Logging) mode enabled
- Foreign key constraints enforced
- Check same thread disabled for multi-threaded access

---

## Error Handling

- Try-except blocks for database operations
- SQLite IntegrityError for duplicate emails
- User-friendly flash messages for all operations
- Graceful fallbacks for missing data

---

## Future Enhancements

Based on research document limitations:
1. Two-factor authentication for enhanced security
2. Dedicated mobile application
3. Advanced real-time features
4. Offline functionality
5. Extended analytics and reporting
6. Video streaming integration
7. Peer-to-peer discussion forums

---

## Testing & Validation

Run system checks:
```powershell
python checks.py
```

This verifies:
- Project files present
- Code compiles without errors
- System ready for deployment

---

## Technology Stack Summary

| Component | Technology |
|-----------|-----------|
| Web Framework | Flask (Python) |
| Database | SQLite3 with WAL |
| Frontend | HTML5, CSS3, Jinja2 |
| Security | Werkzeug (hashing, file handling) |
| File Storage | Local filesystem (`uploads/`) |
| Session Management | Flask sessions (signed cookies) |

---

## Code Quality

All files include:
- ✅ Comprehensive header documentation
- ✅ Function docstrings with descriptions
- ✅ Organized sections with clear comments
- ✅ Descriptive variable names
- ✅ Proper error handling
- ✅ Academic attribution

---

**Last Updated:** February 07, 2026  
**Project Status:** MVP Complete and Documented
