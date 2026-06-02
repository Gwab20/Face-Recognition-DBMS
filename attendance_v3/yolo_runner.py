from ultralytics import YOLO
import cv2
import time

from pg_db import connect_pg, get_cursor

#  SETTINGS
DELAY_SECONDS = 6          # change to 8 if needed
CONF_THRESHOLD = 0.6       # detection confidence threshold

#  CLASS NAME → STUDENT MAPPING
STUDENTS = {
    "Ali": ("2024615", "Ali Akbar"),
    "Abdulrehman": ("2024027", "Abdul Rehman"),
    "Shareq": ("2024465", "Shareq"),
    "Awab": ("2024358", "Awab")
}


#  MARK ATTENDANCE (POSTGRES)
def mark_attendance(name, date, course_id, teacher_id, log_callback, confidence=0.0):
    if name not in STUDENTS:
        # Log unknown/failed scan
        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute(
                "INSERT INTO face_recognition_log (confidence, success) VALUES (%s, FALSE)",
                (round(min(max(confidence, 0.0), 1.0), 4),)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        return

    roll_no, full_name = STUDENTS[name]

    try:
        conn = connect_pg()
        cur = get_cursor(conn)

        cur.execute(
            "SELECT student_id FROM students WHERE roll_number = %s",
            (roll_no,)
        )
        result = cur.fetchone()

        if not result:
            conn.close()
            return

        student_id = result["student_id"]

        cur.execute("""
            INSERT INTO attendance
                (student_id, course_id, attendance_date,
                 status, marked_by, marked_via, check_in_time)
            VALUES (%s, %s, %s, 'present', %s, 'face_id', CURRENT_TIME)
            ON CONFLICT (student_id, course_id, attendance_date)
            DO UPDATE SET
                status        = 'present',
                marked_via    = 'face_id',
                marked_by     = EXCLUDED.marked_by,
                check_in_time = CURRENT_TIME
            RETURNING attendance_id
        """, (student_id, course_id, date, teacher_id))

        row = cur.fetchone()
        attendance_id = row["attendance_id"] if row else None

        # Log to face_recognition_log
        cur.execute("""
            INSERT INTO face_recognition_log
                (student_id, attendance_id, confidence, success)
            VALUES (%s, %s, %s, TRUE)
        """, (student_id, attendance_id, round(min(max(confidence, 0.0), 1.0), 4)))

        # Log to access_log
        cur.execute("""
            INSERT INTO access_log (user_id, action, target_type, target_id)
            VALUES (%s, 'face_id_attendance', 'attendance', %s)
        """, (teacher_id, attendance_id))

        conn.commit()
        conn.close()

        log_callback(f"✅ {full_name} marked present")

    except Exception as e:
        log_callback(f"❌ DB error: {e}")


#  YOLO RUNNER
def run_yolo(selected_date, course_id, teacher_id, log_callback):
    model = YOLO("best.pt")
    cap = cv2.VideoCapture(0)

    # track detection timing
    detection_buffer = {}

    log_callback("📷 Camera started...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        annotated = results[0].plot()

        current_time = time.time()

        if results[0].boxes is not None:
            for box in results[0].boxes:

                confidence = float(box.conf[0])

                # 🔥 CONFIDENCE FILTER
                if confidence < CONF_THRESHOLD:
                    continue

                cls_id = int(box.cls[0])
                name = model.names[cls_id]

                # first detection
                if name not in detection_buffer:
                    detection_buffer[name] = current_time

                elapsed = current_time - detection_buffer[name]

                # 🔥 DELAY LOGIC
                if elapsed >= DELAY_SECONDS:
                    mark_attendance(
                        name,
                        selected_date,
                        course_id,
                        teacher_id,
                        log_callback,
                        confidence=confidence
                    )

                    log_callback(
                        f"🟢 {name} confirmed ({confidence:.2f}) after {int(elapsed)}s"
                    )

                    # prevent re-marking
                    detection_buffer[name] = current_time + 9999

        cv2.imshow("Press Q to quit", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    log_callback("🛑 Camera stopped")