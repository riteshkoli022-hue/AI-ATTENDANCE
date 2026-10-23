"""End-to-end smoke tests for CampusFlow's main role-based flows."""

import unittest
from datetime import date

from werkzeug.security import generate_password_hash

from app import (
    Attendance,
    Lecture,
    Student,
    Subject,
    Teacher,
    User,
    create_app,
    db,
)


class CampusFlowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        with cls.app.app_context():
            teacher_user = User(
                username="test.teacher",
                password_hash=generate_password_hash("TeacherPass123!"),
                role="teacher",
            )
            student_user = User(
                username="test.student",
                password_hash=generate_password_hash("StudentPass123!"),
                role="student",
            )
            db.session.add_all([teacher_user, student_user])
            db.session.flush()

            teacher = Teacher(
                user_id=teacher_user.id,
                teacher_name="Test Teacher",
                department="Computer Science",
            )
            student = Student(
                user_id=student_user.id,
                student_name="Test Student",
                roll_number="TEST-001",
                class_name="FYCS",
                division="A",
            )
            db.session.add_all([teacher, student])
            db.session.flush()

            subject = Subject(
                subject_name="Testing Fundamentals",
                class_name="FYCS",
                division="A",
                teacher_id=teacher.id,
            )
            db.session.add(subject)
            db.session.flush()
            db.session.add(
                Lecture(
                    subject_id=subject.id,
                    teacher_id=teacher.id,
                    class_name="FYCS",
                    division="A",
                    lecture_date=date.today().isoformat(),
                    start_time="00:00",
                    end_time="23:59",
                    attendance_open_time="00:00",
                    attendance_close_time="23:59",
                    room="Test Lab",
                    status="active",
                )
            )
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        self.client = self.app.test_client()

    def login(self, username, password):
        return self.client.post(
            "/login", data={"username": username, "password": password}, follow_redirects=False
        )

    def test_teacher_login_and_main_pages(self):
        response = self.login("test.teacher", "TeacherPass123!")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/teacher/dashboard", response.headers["Location"])
        self.assertEqual(self.client.get("/teacher/dashboard").status_code, 200)
        self.assertEqual(self.client.get("/teacher/lectures").status_code, 200)
        self.assertEqual(self.client.get("/teacher/reports").status_code, 200)

    def test_student_routes_and_teacher_route_protection(self):
        response = self.login("test.student", "StudentPass123!")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/student/dashboard", response.headers["Location"])
        self.assertEqual(self.client.get("/student/dashboard").status_code, 200)
        self.assertEqual(self.client.get("/student/lectures").status_code, 200)
        self.assertEqual(self.client.get("/student/attendance-history").status_code, 200)
        self.assertEqual(self.client.get("/api/campus-settings").status_code, 200)
        self.assertEqual(self.client.get("/teacher/dashboard").status_code, 403)

    def test_teacher_can_create_lecture(self):
        self.login("test.teacher", "TeacherPass123!")
        with self.app.app_context():
            subject = Subject.query.first()
            before = Lecture.query.count()
        response = self.client.post(
            "/teacher/lectures/create",
            data={
                "subject_id": subject.id,
                "lecture_date": date.today().isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
                "attendance_open_time": "10:00",
                "attendance_close_time": "11:00",
                "room": "Room 101",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(Lecture.query.count(), before + 1)

    def test_attendance_requires_a_face_profile_and_blocks_duplicates(self):
        self.login("test.student", "StudentPass123!")
        with self.app.app_context():
            lecture = Lecture.query.filter_by(room="Test Lab").first()
        response = self.client.post(
            f"/attendance/mark/{lecture.id}",
            data={"latitude": "19.076", "longitude": "72.8777", "face_data": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Face profile not registered", response.data)
        with self.app.app_context():
            record = Attendance.query.filter_by(lecture_id=lecture.id).one()
            self.assertEqual(record.status, "rejected")
            self.assertEqual(record.rejection_reason, "Face profile not registered")

        duplicate = self.client.post(
            f"/attendance/mark/{lecture.id}",
            data={"latitude": "19.076", "longitude": "72.8777", "face_data": ""},
        )
        self.assertIn(b"Duplicate attendance", duplicate.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
