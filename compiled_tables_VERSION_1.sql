CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    face_encoding TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE access_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(100),
    target_id INTEGER,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE teachers (
    teacher_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(100),
    phone VARCHAR(20),
    hire_date DATE
);


CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    credits INTEGER NOT NULL,
    teacher_id INTEGER REFERENCES teachers(teacher_id) ON DELETE SET NULL,
    semester VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
);


CREATE TABLE students (
    student_id       SERIAL PRIMARY KEY,
    user_id          INTEGER REFERENCES users(user_id),
    first_name       VARCHAR(100),
    last_name        VARCHAR(100),
    roll_number      VARCHAR(50) UNIQUE,
    date_of_birth    DATE,
    gender           CHAR(1),
    phone            VARCHAR(20),
    address          TEXT,
    enrollment_year  INTEGER,
    current_semester INTEGER,
    is_active        BOOLEAN
);


CREATE TABLE enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER REFERENCES students(student_id),
    course_id       INTEGER REFERENCES courses(course_id),
    enrollment_date DATE
);


CREATE TABLE attendance (
    attendance_id   SERIAL PRIMARY KEY,
    student_id      INTEGER REFERENCES students(student_id),
    course_id       INTEGER REFERENCES courses(course_id),
    attendance_date DATE,
    status          VARCHAR(50),
    marked_by       INTEGER REFERENCES users(user_id),
    marked_via      VARCHAR(50),
    check_in_time   TIME,
    remarks         TEXT
);


Create Table ASSESSMENT_TYPES(
type_id SERIAL PRIMARY KEY,
type_name VARCHAR(50) UNIQUE NOT NULL,
WEIGHT_PERCENTAGE INTEGER NOT NULL
);


CREATE Table ASSESSMENTS(
assessment_id SERIAL PRIMARY KEY,
Title VARCHAR(50) NOT NULL,
Max_score INTEGER NOT NULL,
Assessment_date DATE NOT NULL,
is_published BOOLEAN NOT NULL,
course_id INTEGER NOT NULL,
type_id INTEGER NOT NULL,
FOREIGN KEY(course_id) REFERENCES courses(course_id),
FOREIGN KEY(type_id) REFERENCES ASSESSMENT_TYPES(type_id)
);

CREATE TABLE MARKS(
marks_id SERIAL PRIMARY KEY,
student_id INTEGER NOT NULL,
assessment_id INTEGER NOT NULL,
score DECIMAL NOT NULL,
remarks TEXT,
updated_by INTEGER ,
updated_at TIMESTAMP,
FOREIGN KEY(student_id) REFERENCES students(student_id),
FOREIGN KEY(assessment_id) REFERENCES ASSESSMENTS(assessment_id),
FOREIGN KEY(updated_by) REFERENCES users(user_id)
);

