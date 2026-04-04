--Student Table
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

--Enrollments Table
CREATE TABLE enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER REFERENCES students(student_id),
    course_id       INTEGER REFERENCES courses(course_id),
    enrollment_date DATE
);

--Attendence Table
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