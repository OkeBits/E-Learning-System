# Web-Based E-Learning System

---

## RESEARCH DOCUMENT INFORMATION

```
Republic of the Philippines
West Prime Horizon Institute Inc.
Bachelor of Science in Information Technology
Zamboanga Del Sur

E – LEARNING SYSTEM 
A Research Presented to the Faculty of Bachelor of Information Technology
In Partial Fulfillment of the Requirements for the Course of Methods of Research In Computing

RESEARCHERS:
- JOHN JETHRO P. UBALES
- EVONIE T. BANO
- JAMES B. SUMAGANG
- AIRESLYN O. PASILAN
- ALEXIS B. SUMALINOG

ADVISER:
- RANDY L. CAÑETE

Date: February 07, 2026
```

---

## CHAPTER I: INTRODUCTION

### Background of the Study

The use of technology in education has become increasingly important in senior high school and higher education institutions. Many schools now use web-based systems to support teaching and learning by providing easier access to lessons, learning materials, and academic activities. These systems help improve flexibility and allow students to continue learning beyond regular classroom hours. However, some institutions still rely on traditional teaching methods and printed materials, which limit students' access to learning resources outside the classroom.

Senior high school and college students are expected to develop independent learning skills. Without a web-based e-learning system, students may experience difficulties in reviewing lessons, submitting academic requirements on time, and monitoring their academic progress. Instructors may also face challenges in organizing learning materials, tracking student performance, and evaluating student outputs when using manual or paper-based methods.

Recent studies show that web-based e-learning systems can improve student engagement, learning management, and communication between students and instructors. These systems provide a centralized platform where learning materials, activities, and assessments can be managed efficiently. The effectiveness of such systems depends on proper system design, user accessibility, and reliable internet connectivity.

### Statement of the Problem

Despite advancements in educational technology, some senior high school and college institutions still experience challenges in providing accessible, organized, and flexible learning materials for students. Many learners continue to rely mainly on face-to-face classroom instruction, which may lead to missed lessons, difficulty in reviewing topics, and limited learning opportunities outside regular class hours.

Instructors often encounter difficulties in managing learning materials, monitoring student performance, and evaluating academic outputs when using manual or paper-based methods. The absence of a centralized web-based learning system can result in inefficiencies in lesson delivery, record keeping, and communication between instructors and students.

**Research Questions:**
1. How can a web-based system improve access to learning materials for senior high school and college students?
2. How can instructors efficiently manage lessons, assignments, and assessments online?
3. How can student learning progress and academic performance be effectively tracked?
4. How can administrators manage users and academic content through a centralized system?

### Objectives of the Study

**General Objective:**
Develop a Web-Based E-Learning System for senior high school and college students.

**Specific Objectives:**
1. Provide students with online access to learning materials, activities, and assessments.
2. Enable instructors to upload, manage, and evaluate academic content efficiently.
3. Allow administrators to manage user accounts, subjects, and system data.
4. Track and monitor student learning progress and academic performance.

### Scope and Limitations

**System Features:**
- **User Management:** Administrators can create, update, and manage accounts for instructors and students, ensuring proper access control.
- **Lesson Management:** Instructors can upload, organize, and update lessons in various formats, making learning materials accessible online.
- **Assignments and Online Assessments:** Students can submit assignments and take quizzes or tests online. Instructors can create, monitor, and grade these assessments automatically.
- **Student Progress Tracking:** The system allows instructors and administrators to monitor student activity, submission status, and academic performance in real-time.
- **Communication and Interaction:** Provides a centralized platform where instructors and students can interact for discussions and clarifications.
- **System Accessibility:** Accessible through web browsers on desktops, tablets, and mobile devices.

**Limitations:**
- Internet Requirement: The system depends on a stable internet connection; offline use is not supported.
- Platform Scope: The system is web-based only; no dedicated mobile app is included.
- Security Limitations: While basic login security is implemented, advanced features such as two-factor authentication are not included.
- Institutional Boundaries: The system is designed exclusively for senior high school and college students.
- Development Challenges: During development, challenges included integrating real-time tracking, ensuring user-friendly navigation, and testing across devices and browsers.

### Significance of the Study

**Benefits for:**
- **Students:** Flexible access to lessons, assignments, and assessments with progress tracking capabilities.
- **Instructors:** Efficient lesson management, organization of assignments, online assessments, and simplified student performance monitoring.
- **Administrators:** Easy user account management, course organization, and centralized academic data maintenance.
- **Future Researchers:** Valuable insights and references for future research on web-based e-learning systems.

---

## SYSTEM OVERVIEW

### Project Description

Minimal e-learning platform built with Flask and SQLite. Features include user roles (admin/teacher/student), courses, lessons, assignments, submissions, quizzes, grading, and simple progress tracking.

---

## INSTALLATION & SETUP GUIDE

### Prerequisites
- Python 3.8 or newer installed and available on PATH
- Windows PowerShell or Command Prompt
- SQLite (included with Python)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Quick Start (Windows PowerShell)

Open PowerShell in the `e_learning` folder and run:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app listens on **http://127.0.0.1:5000** by default.

### Database Setup

The application will automatically create `database.db` in the `e_learning` folder using `schema.sql` on first run. 

**File Storage:**
- Uploaded files are stored in the `uploads/` folder
- Ensure the `uploads/` directory exists and has write permissions

### User Management

#### Register Users
1. Navigate to `/register` in your browser
2. Choose your role: **Admin**, **Teacher**, or **Student**
3. Complete the registration form

#### Create Admin User

**Method 1: Command Line Script**

Use the create_admin.py script:

```powershell
python create_admin.py
```

**Method 2: Database Query (PowerShell)**

Run this Python one-liner from the `e_learning` folder (replace the email):

```powershell
python - <<'PY'
import sqlite3
db='database.db'
conn=sqlite3.connect(db)
email='your-email@example.com'
conn.execute("UPDATE users SET role='admin' WHERE email=?", (email,))
conn.commit()
conn.close()
print('Updated role for', email)
PY
```

**Method 3: SQLite Editor**

Directly edit the database using any SQLite editor and set `role='admin'` for your user row in the `users` table.

---

## SYSTEM ARCHITECTURE

### Technology Stack

- **Backend:** Flask (Python web framework)
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, Jinja2 Templates
- **Security:** Werkzeug (password hashing)
- **File Handling:** Werkzeug (secure filename handling)

### Database Schema

Key tables include:
- `users` - User accounts and roles (admin, teacher, student)
- `courses` - Course information and metadata
- `lessons` - Lesson content organized by course
- `assignments` - Assignment definitions
- `submissions` - Student assignment submissions
- `quizzes` - Quiz definitions and questions
- `grades` - Student grades and assessments
- `deleted_users` - Audit trail for deleted user accounts

---

## KEY FEATURES

### For Students
- ✓ Browse and enroll in courses
- ✓ Access lesson materials and resources
- ✓ Submit assignments with file uploads
- ✓ Take online quizzes and tests
- ✓ View grades and feedback
- ✓ Track learning progress
- ✓ Update profile information

### For Instructors/Teachers
- ✓ Create and manage courses
- ✓ Upload and organize lessons
- ✓ Create assignments with deadlines
- ✓ Design and conduct online quizzes
- ✓ Review student submissions
- ✓ Grade assignments and quizzes
- ✓ Monitor student performance
- ✓ Generate progress reports

### For Administrators
- ✓ Manage user accounts (create, edit, delete)
- ✓ Create and organize courses
- ✓ Manage course instructors and students
- ✓ Monitor system usage and activity
- ✓ Audit deleted user records
- ✓ Maintain system data integrity
- ✓ Generate administrative reports

---

## DEFINITION OF KEY TERMS

| Term | Definition |
|------|-----------|
| **E-Learning** | A learning method that uses electronic technologies and online platforms to deliver educational content and facilitate learning outside the traditional classroom. |
| **Web-Based System** | A software application that can be accessed and operated through a web browser, allowing users to interact and perform tasks online. |
| **Administrator** | A user role in the system responsible for managing user accounts, courses, and overall system operations. |
| **Instructor** | A user role in the system responsible for uploading lessons, creating assignments, conducting assessments, and monitoring student performance. |
| **Student** | A user role in the system who accesses learning materials, submits assignments, takes online assessments, and tracks their academic progress. |
| **Lesson Management** | The process of creating, uploading, organizing, and updating learning materials within the system for student access. |
| **Assignment Submission** | The process by which students submit academic tasks or homework online through the system. |
| **Online Assessment** | Tests, quizzes, or exams conducted through the web-based platform to evaluate student understanding and performance. |
| **Progress Tracking** | A feature of the system that allows instructors and administrators to monitor student activities, submissions, and performance in real-time. |
| **User Management** | Administrative functions that include creating, updating, and deleting user accounts, and assigning roles and permissions. |
| **System Accessibility** | The ability of the system to be accessed from various devices (desktop, tablet, mobile) using a web browser and internet connection. |
| **Centralized Platform** | A single online system where all users, content, and academic data are organized and managed in one location. |
| **Academic Performance** | The measurable outcomes of student learning, including grades, assessment scores, and completion of academic tasks. |

---

## TROUBLESHOOTING

### Common Issues

**Port Already in Use:**
If port 5000 is already in use, modify the app.py to run on a different port:
```python
app.run(debug=True, port=5001)
```

**Database Locked:**
The system uses WAL (Write-Ahead Logging) mode for better concurrency. If you experience locks, ensure only one instance of the application is running.

**File Upload Issues:**
- Verify the `uploads/` folder exists and has write permissions
- Check file size limitations in configuration
- Ensure uploaded filenames are properly sanitized

---

## REFERENCES (2022–PRESENT, IEEE STYLE)

[1] E. J. R. Malabanan, "Leading the digital school: Exploring the relationship between learning management system practices and school leadership in senior high schools," American Journal of Education and Technology, vol. 4, no. 3, pp. 71–78, 2025.

[2] S. Getenet, R. Cantle, P. Redmond, et al., "Students' digital technology attitude, literacy and self-efficacy and their effect on online learning engagement," International Journal of Educational Technology in Higher Education, vol. 21, art. 3, 2024.

[3] "Analysis of online learning issues within the higher education quality assurance frame," Education Sciences, vol. 13, no. 12, 2023.

[4] S. Getenet, R. Cantle, P. Redmond, et al., "Students' digital technology attitude, literacy and self-efficacy and their effect on online learning engagement," International Journal of Educational Technology in Higher Education, vol. 21, art. 3, 2024.

[5] E. J. R. Malabanan, "Leading the digital school: Exploring the relationship between learning management system practices and school leadership in senior high schools," American Journal of Education and Technology, vol. 4, no. 3, pp. 71–78, 2025.

---

## PROJECT INFORMATION

**Created by:** JOHN JETHRO P. UBALES, EVONIE T. BANO, JAMES B. SUMAGANG, AIRESLYN O. PASILAN, ALEXIS B. SUMALINOG

**Adviser:** RANDY L. CAÑETE

**Institution:** West Prime Horizon Institute Inc., Bachelor of Science in Information Technology, Zamboanga Del Sur

**Date:** February 07, 2026

**Version:** MVP (Minimum Viable Product)

```powershell
python create_admin.py
```

Run script
----------
There's a helper PowerShell script to quickly start the app: `run_local.ps1`.

Exporting submissions
---------------------
Teachers and admins can export assignment submissions as CSV via the assignment detail page (uses `/assignment/<id>/export`).

Notes & Troubleshooting
-----------------------
- If `python` is not recognized in PowerShell, ensure Python is installed and "Add Python to PATH" was selected during install. You can also run using a full path to the Python executable.
- This project uses a simple dev secret key in `app.py`; replace `app.config['SECRET_KEY']` with a secure value for production.

Next steps
----------
- Improve authentication (session security, password reset)
- Add pagination and richer UI
- Add tests and CI for automated checks
