"""Create clearly fictional demo users, subjects, and sample lectures."""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import create_app, db, User, Teacher, Student, Subject, Lecture

app=create_app()
with app.app_context():
    if User.query.filter_by(username='teacher.demo').first():
        print('Demo data already exists. No changes made.'); raise SystemExit(0)
    teacher_user=User(username='teacher.demo',password_hash=generate_password_hash('TeachDemo123!'),role='teacher')
    student_a_user=User(username='student.asha',password_hash=generate_password_hash('Student123!'),role='student')
    student_b_user=User(username='student.kabir',password_hash=generate_password_hash('Student123!'),role='student')
    db.session.add_all([teacher_user,student_a_user,student_b_user]);db.session.flush()
    teacher=Teacher(user_id=teacher_user.id,teacher_name='Demo Teacher',department='Computer Science')
    db.session.add(teacher);db.session.flush()
    db.session.add_all([
      Student(user_id=student_a_user.id,student_name='Asha Demo',roll_number='DEMO-001',class_name='FYCS',division='A'),
      Student(user_id=student_b_user.id,student_name='Kabir Demo',roll_number='DEMO-002',class_name='FYCS',division='A')])
    db.session.flush()
    subjects=[Subject(subject_name='Programming Fundamentals',class_name='FYCS',division='A',teacher_id=teacher.id),Subject(subject_name='Digital Systems',class_name='FYCS',division='A',teacher_id=teacher.id)]
    db.session.add_all(subjects);db.session.flush()
    today=date.today()
    for offset,subject,start,end in [(0,subjects[0],'09:00','10:00'),(0,subjects[1],'11:00','12:00'),(1,subjects[0],'09:00','10:00'),(2,subjects[1],'11:00','12:00')]:
        db.session.add(Lecture(subject_id=subject.id,teacher_id=teacher.id,class_name=subject.class_name,division=subject.division,lecture_date=(today+timedelta(days=offset)).isoformat(),start_time=start,end_time=end,attendance_open_time=start,attendance_close_time=end,room='Room 204',status='active'))
    db.session.commit()
    print('Demo data created. Teacher: teacher.demo / TeachDemo123!')
    print('Students: student.asha and student.kabir / Student123!')
