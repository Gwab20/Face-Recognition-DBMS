--  STUDENT RECORD SYSTEM 

--  DROP EXISTING TABLES 
DROP TABLE IF EXISTS face_recognition_log CASCADE;
DROP TABLE IF EXISTS marks               CASCADE;
DROP TABLE IF EXISTS assessments         CASCADE;
DROP TABLE IF EXISTS assessment_types    CASCADE;
DROP TABLE IF EXISTS attendance          CASCADE;
DROP TABLE IF EXISTS enrollments         CASCADE;
DROP TABLE IF EXISTS students            CASCADE;
DROP TABLE IF EXISTS courses             CASCADE;
DROP TABLE IF EXISTS teachers            CASCADE;
DROP TABLE IF EXISTS access_log          CASCADE;
DROP TABLE IF EXISTS users               CASCADE;


--  TABLES

-- USERS
CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('teacher', 'student')),
    face_encoding TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ACCESS LOG
CREATE TABLE access_log (
    log_id      SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    action      VARCHAR(100) NOT NULL,
    target_type VARCHAR(100),
    target_id   INTEGER,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TEACHERS
CREATE TABLE teachers (
    teacher_id  SERIAL PRIMARY KEY,
    user_id     INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50)  UNIQUE NOT NULL,
    department  VARCHAR(100),
    phone       VARCHAR(20),
    hire_date   DATE
);

-- COURSES
CREATE TABLE courses (
    course_id   SERIAL PRIMARY KEY,
    course_code VARCHAR(20)  UNIQUE NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    credits     INTEGER      NOT NULL CHECK (credits > 0),
    teacher_id  INTEGER REFERENCES teachers(teacher_id) ON DELETE SET NULL,
    semester    VARCHAR(20),
    is_active   BOOLEAN DEFAULT TRUE
);

-- STUDENTS
CREATE TABLE students (
    student_id       SERIAL PRIMARY KEY,
    user_id          INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    roll_number      VARCHAR(50)  UNIQUE NOT NULL,
    date_of_birth    DATE,
    gender           CHAR(1) CHECK (gender IN ('M', 'F')),
    phone            VARCHAR(20),
    address          TEXT,
    enrollment_year  INTEGER,
    current_semester INTEGER CHECK (current_semester > 0),
    is_active        BOOLEAN DEFAULT TRUE
);

-- ENROLLMENTS
CREATE TABLE enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id)   ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    UNIQUE (student_id, course_id)
);

-- ATTENDANCE
CREATE TABLE attendance (
    attendance_id   SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id)   ON DELETE CASCADE,
    attendance_date DATE    NOT NULL,
    status          VARCHAR(10) NOT NULL CHECK (status IN ('present', 'absent')),
    marked_by       INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    marked_via      VARCHAR(20) CHECK (marked_via IN ('face_id', 'manual')),
    check_in_time   TIME,
    remarks         TEXT,
    UNIQUE (student_id, course_id, attendance_date)
);

-- FACE RECOGNITION LOG
CREATE TABLE face_recognition_log (
    log_id        SERIAL PRIMARY KEY,
    student_id    INTEGER REFERENCES students(student_id) ON DELETE SET NULL,
    attendance_id INTEGER REFERENCES attendance(attendance_id) ON DELETE SET NULL,
    confidence    DECIMAL(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    recognized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address    INET,
    success       BOOLEAN NOT NULL DEFAULT FALSE
);

-- ASSESSMENT TYPES
CREATE TABLE assessment_types (
    type_id           SERIAL PRIMARY KEY,
    type_name         VARCHAR(50) UNIQUE NOT NULL,
    weight_percentage DECIMAL(5,2) NOT NULL CHECK (weight_percentage > 0 AND weight_percentage <= 100)
);

-- ASSESSMENTS
CREATE TABLE assessments (
    assessment_id   SERIAL PRIMARY KEY,
    title           VARCHAR(100) NOT NULL,
    max_score       INTEGER      NOT NULL CHECK (max_score > 0),
    assessment_date DATE         NOT NULL,
    is_published    BOOLEAN      NOT NULL DEFAULT FALSE,
    course_id       INTEGER      NOT NULL REFERENCES courses(course_id)        ON DELETE CASCADE,
    type_id         INTEGER      NOT NULL REFERENCES assessment_types(type_id) ON DELETE RESTRICT
);

-- MARKS
CREATE TABLE marks (
    mark_id       SERIAL PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students(student_id)      ON DELETE CASCADE,
    assessment_id INTEGER NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    score         DECIMAL(6,2) NOT NULL CHECK (score >= 0),
    remarks       TEXT,
    updated_by    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, assessment_id)
);


--  INDEXES
CREATE INDEX idx_attendance_student  ON attendance(student_id);
CREATE INDEX idx_attendance_course   ON attendance(course_id);
CREATE INDEX idx_attendance_date     ON attendance(attendance_date);
CREATE INDEX idx_marks_student       ON marks(student_id);
CREATE INDEX idx_marks_assessment    ON marks(assessment_id);
CREATE INDEX idx_face_log_student    ON face_recognition_log(student_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course  ON enrollments(course_id);


--  SEED DATA
--  All passwords are bcrypt hash of: password123

-- USERS
INSERT INTO users (user_id, email, password_hash, role) VALUES
(1, 'ali.akber@giki.edu.pk', '$2b$12$0sFVRuBJJwemVM7ko.Z9ZOEAMkVHHfRfsfUS3rPvujbmT3gsuZ8Mi', 'teacher'),
(2, '2024358@giki.edu.pk',   '$2b$12$0sFVRuBJJwemVM7ko.Z9ZOEAMkVHHfRfsfUS3rPvujbmT3gsuZ8Mi', 'student'),
(3, '2024027@giki.edu.pk',   '$2b$12$0sFVRuBJJwemVM7ko.Z9ZOEAMkVHHfRfsfUS3rPvujbmT3gsuZ8Mi', 'student'),
(4, '2024465@giki.edu.pk',   '$2b$12$0sFVRuBJJwemVM7ko.Z9ZOEAMkVHHfRfsfUS3rPvujbmT3gsuZ8Mi', 'student');

-- Reset sequence so future INSERTs don't collide
SELECT setval('users_user_id_seq', 4);

-- TEACHER
INSERT INTO teachers (teacher_id, user_id, first_name, last_name, employee_id, department, phone, hire_date) VALUES
(1, 1, 'Ali', 'Akber', 'EMP-001', 'Computer Science', '03055512111', '2020-01-15');

SELECT setval('teachers_teacher_id_seq', 1);

-- COURSES
INSERT INTO courses (course_id, course_code, course_name, credits, teacher_id, semester, is_active) VALUES
(1, 'C232',  'Database Management Systems', 3, 1, 'Spring 2025', TRUE),
(2, 'CS102', 'Object Oriented Programming', 3, 1, 'Spring 2025', TRUE);

SELECT setval('courses_course_id_seq', 2);

-- STUDENTS
INSERT INTO students (student_id, user_id, first_name, last_name, roll_number, date_of_birth, gender, phone, enrollment_year, current_semester, is_active) VALUES
(1, 2, 'Muhammad', 'Awab',   '2024358', '2004-12-27', 'M', '03011111111', 2024, 4, TRUE),
(2, 3, 'Abdul',    'Rehman', '2024027', '2000-08-24', 'M', '03022222222', 2024, 4, TRUE),
(3, 4, 'Shariq',   'Usman',  '2024465', '2001-09-11', 'M', '03033333333', 2024, 4, TRUE);

SELECT setval('students_student_id_seq', 3);

-- ENROLLMENTS
INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES
(1, 1, '2025-01-20'),
(1, 2, '2025-01-20'),
(2, 1, '2025-01-20'),
(2, 2, '2025-01-20'),
(3, 1, '2025-01-20'),
(3, 2, '2025-01-20');

-- ASSESSMENT TYPES
INSERT INTO assessment_types (type_id, type_name, weight_percentage) VALUES
(1, 'Quiz',       10.00),
(2, 'Assignment', 15.00),
(3, 'Midterm',    35.00),
(4, 'Final',      40.00);

SELECT setval('assessment_types_type_id_seq', 4);

-- ASSESSMENTS
INSERT INTO assessments (assessment_id, title, max_score, assessment_date, is_published, course_id, type_id) VALUES
(1, 'Quiz 1',       20,  '2025-02-10', TRUE, 1, 1),
(2, 'Assignment 1', 50,  '2025-02-20', TRUE, 1, 2),
(3, 'Midterm',      100, '2025-03-05', TRUE, 1, 3),
(4, 'Quiz 1',       20,  '2025-02-12', TRUE, 2, 1),
(5, 'Assignment 1', 50,  '2025-02-22', TRUE, 2, 2);

SELECT setval('assessments_assessment_id_seq', 5);

-- MARKS
INSERT INTO marks (student_id, assessment_id, score, remarks, updated_by) VALUES
(1, 1, 17.00, 'Good attempt',            1),
(1, 2, 44.00, NULL,                      1),
(1, 3, 99.00, 'Top of class',            1),
(1, 4, 16.00, NULL,                      1),
(1, 5, 40.00, NULL,                      1),
(2, 1, 14.00, NULL,                      1),
(2, 2, 38.00, 'Needs improvement',       1),
(2, 3, 70.00, NULL,                      1),
(2, 4, 18.00, 'Excellent',               1),
(2, 5, 45.00, NULL,                      1),
(3, 1, 19.00, 'Nearly perfect',          1),
(3, 2, 47.00, NULL,                      1),
(3, 3, 88.00, 'Blow up with excitement', 1),
(3, 4, 15.00, NULL,                      1),
(3, 5, 42.00, NULL,                      1);

-- ATTENDANCE
INSERT INTO attendance (student_id, course_id, attendance_date, status, marked_by, marked_via, check_in_time) VALUES
-- C232 DBMS — Week 1
(1, 1, '2025-02-03', 'present', 1, 'face_id', '09:02:00'),
(2, 1, '2025-02-03', 'present', 1, 'face_id', '09:04:00'),
(3, 1, '2025-02-03', 'present', 1, 'face_id', '09:01:00'),

(1, 1, '2025-02-05', 'present', 1, 'face_id', '09:00:00'),
(2, 1, '2025-02-05', 'absent',  1, 'manual',  NULL),
(3, 1, '2025-02-05', 'present', 1, 'face_id', '09:03:00'),

(1, 1, '2025-02-07', 'present', 1, 'face_id', '09:05:00'),
(2, 1, '2025-02-07', 'present', 1, 'face_id', '09:02:00'),
(3, 1, '2025-02-07', 'absent',  1, 'manual',  NULL),

-- C232 DBMS — Week 2
(1, 1, '2025-02-10', 'present', 1, 'face_id', '09:01:00'),
(2, 1, '2025-02-10', 'present', 1, 'face_id', '09:06:00'),
(3, 1, '2025-02-10', 'present', 1, 'face_id', '09:00:00'),

(1, 1, '2025-02-12', 'absent',  1, 'manual',  NULL),
(2, 1, '2025-02-12', 'present', 1, 'face_id', '09:03:00'),
(3, 1, '2025-02-12', 'present', 1, 'face_id', '09:02:00'),

-- CS102 OOP — Week 1
(1, 2, '2025-02-04', 'present', 1, 'face_id', '11:00:00'),
(2, 2, '2025-02-04', 'present', 1, 'face_id', '11:02:00'),
(3, 2, '2025-02-04', 'present', 1, 'face_id', '11:01:00'),

(1, 2, '2025-02-06', 'present', 1, 'face_id', '11:03:00'),
(2, 2, '2025-02-06', 'absent',  1, 'manual',  NULL),
(3, 2, '2025-02-06', 'present', 1, 'face_id', '11:00:00'),

-- CS102 OOP — Week 2
(1, 2, '2025-02-11', 'present', 1, 'face_id', '11:01:00'),
(2, 2, '2025-02-11', 'present', 1, 'face_id', '11:04:00'),
(3, 2, '2025-02-11', 'present', 1, 'face_id', '11:00:00'),

(1, 2, '2025-02-13', 'present', 1, 'face_id', '11:02:00'),
(2, 2, '2025-02-13', 'present', 1, 'face_id', '11:01:00'),
(3, 2, '2025-02-13', 'absent',  1, 'manual',  NULL);




SELECT * FROM users;
SELECT * FROM teachers;
SELECT * FROM students;
SELECT * FROM courses;
SELECT * FROM enrollments;
SELECT * FROM attendance;
SELECT * FROM face_recognition_log;
SELECT * FROM assessment_types;
SELECT * FROM assessments;
SELECT * FROM marks;
SELECT * FROM access_log;