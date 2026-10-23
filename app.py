from datetime import datetime, date, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from services.face_service import encode_face, verify_face, FaceError
from services.attendance_service import check_attendance

db = SQLAlchemy()
csrf = CSRFProtect()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    student_name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(40), unique=True, nullable=False)
    class_name = db.Column(db.String(40), nullable=False)
    division = db.Column(db.String(20), nullable=False)
    face_profile = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User')
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User')
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(120), nullable=False)
    class_name = db.Column(db.String(40), nullable=False)
    division = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship('Teacher')
class Lecture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False, index=True)
    class_name = db.Column(db.String(40), nullable=False)
    division = db.Column(db.String(20), nullable=False)
    lecture_date = db.Column(db.String(10), nullable=False, index=True)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    attendance_open_time = db.Column(db.String(5), nullable=False)
    attendance_close_time = db.Column(db.String(5), nullable=False)
    room = db.Column(db.String(80))
    status = db.Column(db.String(16), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    distance_from_campus = db.Column(db.Float)
    face_verified = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    rejection_reason = db.Column(db.String(160))
    lecture = db.relationship('Lecture')
    student = db.relationship('Student')
    __table_args__ = (db.UniqueConstraint('lecture_id', 'student_id', name='unique_student_lecture_attendance'),)
class CampusSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius_meters = db.Column(db.Float, nullable=False)
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.String(240), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

def seed_demo_data():
    """Create missing fictional demo records without overwriting existing accounts."""
    demo_users = (
        ("teacher.demo", "TeachDemo123!", "teacher"),
        ("student.asha", "Student123!", "student"),
        ("student.kabir", "Student123!", "student"),
    )
    users = {}
    for username, password, role in demo_users:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, password_hash=generate_password_hash(password), role=role)
            db.session.add(user)
            db.session.flush()
        elif user.role != role:
            raise RuntimeError(f"Demo username {username!r} is already assigned to a different role.")
        users[username] = user

    teacher = Teacher.query.filter_by(user_id=users["teacher.demo"].id).first()
    if teacher is None:
        teacher = Teacher(user_id=users["teacher.demo"].id, teacher_name="Demo Teacher", department="Computer Science")
        db.session.add(teacher)
        db.session.flush()

    for username, name, roll_number in (
        ("student.asha", "Asha Demo", "DEMO-001"),
        ("student.kabir", "Kabir Demo", "DEMO-002"),
    ):
        if Student.query.filter_by(user_id=users[username].id).first() is None:
            db.session.add(Student(user_id=users[username].id, student_name=name, roll_number=roll_number, class_name="FYCS", division="A"))

    subjects = {}
    for subject_name in ("Programming Fundamentals", "Digital Systems"):
        subject = Subject.query.filter_by(subject_name=subject_name, class_name="FYCS", division="A", teacher_id=teacher.id).first()
        if subject is None:
            subject = Subject(subject_name=subject_name, class_name="FYCS", division="A", teacher_id=teacher.id)
            db.session.add(subject)
            db.session.flush()
        subjects[subject_name] = subject

    today = date.today()
    lecture_specs = (
        (0, "Programming Fundamentals", "09:00", "10:00"),
        (0, "Digital Systems", "11:00", "12:00"),
        (1, "Programming Fundamentals", "09:00", "10:00"),
        (2, "Digital Systems", "11:00", "12:00"),
    )
    for offset, subject_name, start, end in lecture_specs:
        lecture_date = (today + timedelta(days=offset)).isoformat()
        subject = subjects[subject_name]
        if Lecture.query.filter_by(subject_id=subject.id, teacher_id=teacher.id, lecture_date=lecture_date, start_time=start).first() is None:
            db.session.add(Lecture(subject_id=subject.id, teacher_id=teacher.id, class_name="FYCS", division="A", lecture_date=lecture_date, start_time=start, end_time=end, attendance_open_time=start, attendance_close_time=end, room="Room 204", status="active"))
    db.session.commit()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    (Path(__file__).resolve().parent / 'instance').mkdir(parents=True, exist_ok=True)
    Path(app.config['FACE_UPLOAD_DIR']).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)
    with app.app_context():
        db.create_all()
        if not CampusSettings.query.first():
            db.session.add(CampusSettings(latitude=app.config['COLLEGE_LATITUDE'], longitude=app.config['COLLEGE_LONGITUDE'], radius_meters=app.config['GEOFENCE_RADIUS_METERS']))
            db.session.commit()
        if app.config['SEED_DEMO_DATA']:
            seed_demo_data()

    @app.context_processor
    def inject_user():
        user = db.session.get(User, session.get('user_id')) if session.get('user_id') else None
        return {'current_user': user, 'now_date': date.today().strftime('%d %b %Y')}

    def login_required(role=None):
        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                user = db.session.get(User, session.get('user_id')) if session.get('user_id') else None
                if not user:
                    flash('Please log in to continue.', 'error')
                    return redirect(url_for('login'))
                if role and user.role != role:
                    abort(403)
                return fn(*args, **kwargs)
            return wrapped
        return decorator

    def teacher_for_user(user):
        return Teacher.query.filter_by(user_id=user.id).first_or_404()

    @app.get('/')
    def home():
        if session.get('user_id'):
            user = db.session.get(User, session['user_id'])
            return redirect(url_for('teacher_dashboard' if user and user.role == 'teacher' else 'student_dashboard'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            role = request.form.get('role', 'student')
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            name = request.form.get('name', '').strip()
            if role != 'student':
                flash('Self-registration is available for students only. Teacher accounts are created by the demo setup.', 'error')
            elif not username or len(password) < 8 or not name:
                flash('Enter your name, username, and a password of at least 8 characters.', 'error')
            elif User.query.filter_by(username=username).first():
                flash('That username is already in use.', 'error')
            else:
                user = User(username=username, password_hash=generate_password_hash(password), role='student')
                db.session.add(user); db.session.flush()
                db.session.add(Student(user_id=user.id, student_name=name, roll_number=request.form.get('roll_number','').strip(), class_name=request.form.get('class_name','').strip(), division=request.form.get('division','').strip()))
                try:
                    db.session.commit(); flash('Account created. You can now log in.', 'success'); return redirect(url_for('login'))
                except Exception:
                    db.session.rollback(); flash('Please check your roll number and profile details; they may already exist.', 'error')
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form.get('username','').strip().lower()).first()
            if user and check_password_hash(user.password_hash, request.form.get('password','')):
                session.clear(); session['user_id'] = user.id
                return redirect(url_for('teacher_dashboard' if user.role == 'teacher' else 'student_dashboard'))
            flash('Invalid username or password.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear(); flash('You have been logged out.', 'success'); return redirect(url_for('login'))

    @app.get('/teacher/dashboard')
    @login_required('teacher')
    def teacher_dashboard():
        teacher = teacher_for_user(db.session.get(User, session['user_id']))
        lectures = Lecture.query.filter_by(teacher_id=teacher.id).order_by(Lecture.lecture_date.desc(), Lecture.start_time).limit(8).all()
        total = Lecture.query.filter_by(teacher_id=teacher.id).count()
        today = Lecture.query.filter_by(teacher_id=teacher.id, lecture_date=date.today().isoformat()).count()
        present = Attendance.query.join(Lecture).filter(Lecture.teacher_id==teacher.id, Attendance.status=='present').count()
        return render_template('teacher_dashboard.html', lectures=lectures, total=total, today=today, present=present)

    @app.route('/teacher/settings/campus', methods=['GET', 'POST'])
    @login_required('teacher')
    def campus_settings_page():
        settings = CampusSettings.query.first()
        if request.method == 'POST':
            try:
                latitude = float(request.form.get('latitude', ''))
                longitude = float(request.form.get('longitude', ''))
                radius = float(request.form.get('radius_meters', ''))
            except ValueError:
                flash('Enter valid numbers for latitude, longitude, and radius.', 'error')
                return render_template('campus_settings.html', settings=settings)
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180 and 1 <= radius <= 50000):
                flash('Latitude must be -90 to 90, longitude -180 to 180, and radius 1 to 50,000 meters.', 'error')
                return render_template('campus_settings.html', settings=settings)
            if settings is None:
                settings = CampusSettings()
            settings.latitude = latitude
            settings.longitude = longitude
            settings.radius_meters = radius
            db.session.add(settings)
            db.session.add(AuditLog(user_id=session['user_id'], action='campus_settings_updated', detail=f'Geofence updated to {radius:g} m radius'))
            db.session.commit()
            flash('Campus location saved. It will apply to new attendance checks immediately.', 'success')
            return redirect(url_for('campus_settings_page'))
        return render_template('campus_settings.html', settings=settings)

    @app.get('/teacher/lectures')
    @login_required('teacher')
    def teacher_lectures():
        teacher = teacher_for_user(db.session.get(User, session['user_id']))
        return render_template('teacher_lectures.html', lectures=Lecture.query.filter_by(teacher_id=teacher.id).order_by(Lecture.lecture_date.desc()).all())

    def lecture_form(lecture=None):
        teacher = teacher_for_user(db.session.get(User, session['user_id']))
        subjects = Subject.query.filter_by(teacher_id=teacher.id).order_by(Subject.subject_name).all()
        if request.method == 'POST':
            subject = Subject.query.filter_by(id=request.form.get('subject_id', type=int), teacher_id=teacher.id).first()
            try:
                day = datetime.strptime(request.form.get('lecture_date',''), '%Y-%m-%d').date()
                start = datetime.strptime(request.form.get('start_time',''), '%H:%M').time()
                end = datetime.strptime(request.form.get('end_time',''), '%H:%M').time()
                opening = datetime.strptime(request.form.get('attendance_open_time',''), '%H:%M').time()
                closing = datetime.strptime(request.form.get('attendance_close_time',''), '%H:%M').time()
            except ValueError:
                flash('Enter valid date and times.', 'error'); return render_template('lecture_form.html', lecture=lecture, subjects=subjects)
            if not subject or end <= start or closing < opening or opening < start or closing > end:
                flash('Choose one of your subjects and keep the attendance window within the lecture time.', 'error')
                return render_template('lecture_form.html', lecture=lecture, subjects=subjects)
            if lecture is None:
                lecture = Lecture(teacher_id=teacher.id)
            lecture.subject_id=subject.id; lecture.class_name=subject.class_name; lecture.division=subject.division
            lecture.lecture_date=day.isoformat(); lecture.start_time=start.strftime('%H:%M'); lecture.end_time=end.strftime('%H:%M')
            lecture.attendance_open_time=opening.strftime('%H:%M'); lecture.attendance_close_time=closing.strftime('%H:%M')
            lecture.room=request.form.get('room','').strip()[:80]; lecture.status='active'
            db.session.add(lecture); db.session.add(AuditLog(user_id=session['user_id'], action='lecture_saved', detail=f'Lecture #{lecture.id or "new"} saved'))
            db.session.commit(); flash('Lecture saved.', 'success'); return redirect(url_for('teacher_lectures'))
        return render_template('lecture_form.html', lecture=lecture, subjects=subjects)

    @app.route('/teacher/lectures/create', methods=['GET','POST'])
    @login_required('teacher')
    def create_lecture(): return lecture_form()

    @app.route('/teacher/lectures/<int:lecture_id>/edit', methods=['GET','POST'])
    @login_required('teacher')
    def edit_lecture(lecture_id):
        teacher=teacher_for_user(db.session.get(User,session['user_id']))
        lecture=Lecture.query.filter_by(id=lecture_id, teacher_id=teacher.id).first_or_404()
        return lecture_form(lecture)

    @app.post('/teacher/lectures/<int:lecture_id>/cancel')
    @login_required('teacher')
    def cancel_lecture(lecture_id):
        teacher=teacher_for_user(db.session.get(User,session['user_id']))
        lecture=Lecture.query.filter_by(id=lecture_id, teacher_id=teacher.id).first_or_404(); lecture.status='cancelled'
        db.session.add(AuditLog(user_id=session['user_id'], action='lecture_cancelled', detail=f'Lecture #{lecture.id} cancelled')); db.session.commit()
        flash('Lecture cancelled.', 'success'); return redirect(url_for('teacher_lectures'))

    @app.post('/teacher/lectures/<int:lecture_id>/delete')
    @login_required('teacher')
    def delete_lecture(lecture_id):
        teacher=teacher_for_user(db.session.get(User,session['user_id']))
        lecture=Lecture.query.filter_by(id=lecture_id, teacher_id=teacher.id).first_or_404()
        if Attendance.query.filter_by(lecture_id=lecture.id).first():
            lecture.status='cancelled'; flash('This lecture has attendance records, so it was cancelled instead of deleted.', 'success')
        else:
            db.session.delete(lecture); flash('Lecture deleted.', 'success')
        db.session.add(AuditLog(user_id=session['user_id'], action='lecture_deleted_or_cancelled', detail=f'Lecture #{lecture_id}')); db.session.commit()
        return redirect(url_for('teacher_lectures'))

    @app.get('/teacher/lectures/<int:lecture_id>/attendance')
    @login_required('teacher')
    def teacher_attendance(lecture_id):
        teacher=teacher_for_user(db.session.get(User,session['user_id']))
        lecture=Lecture.query.filter_by(id=lecture_id, teacher_id=teacher.id).first_or_404()
        records=Attendance.query.filter_by(lecture_id=lecture.id).order_by(Attendance.marked_at.desc()).all()
        return render_template('teacher_attendance.html', lecture=lecture, records=records)

    @app.route('/teacher/reports', methods=['GET','POST'])
    @login_required('teacher')
    def reports():
        teacher=teacher_for_user(db.session.get(User,session['user_id']))
        query=Attendance.query.join(Lecture).join(Student).filter(Lecture.teacher_id==teacher.id)
        if request.values.get('date'): query=query.filter(Lecture.lecture_date==request.values['date'])
        if request.values.get('class_name'): query=query.filter(Lecture.class_name==request.values['class_name'])
        if request.values.get('division'): query=query.filter(Lecture.division==request.values['division'])
        if request.values.get('student'): query=query.filter(Student.student_name.ilike(f"%{request.values['student']}%"))
        records=query.order_by(Lecture.lecture_date.desc()).all()
        return render_template('reports.html', records=records)

    @app.post('/teacher/attendance/<int:record_id>/correct')
    @login_required('teacher')
    def correct_attendance(record_id):
        teacher=teacher_for_user(db.session.get(User,session['user_id']))
        record=Attendance.query.join(Lecture).filter(Attendance.id==record_id, Lecture.teacher_id==teacher.id).first_or_404()
        status=request.form.get('status')
        if status not in ('present','rejected'): abort(400)
        record.status=status; record.rejection_reason=None if status=='present' else 'Teacher correction'
        db.session.add(AuditLog(user_id=session['user_id'],action='attendance_corrected',detail=f'Record #{record.id} set to {status}')); db.session.commit()
        flash('Attendance correction saved and audited.', 'success'); return redirect(url_for('teacher_attendance',lecture_id=record.lecture_id))

    @app.get('/student/dashboard')
    @login_required('student')
    def student_dashboard():
        user=db.session.get(User,session['user_id']); student=Student.query.filter_by(user_id=user.id).first_or_404()
        lectures=Lecture.query.filter_by(class_name=student.class_name, division=student.division, lecture_date=date.today().isoformat()).order_by(Lecture.start_time).all()
        total=Attendance.query.filter_by(student_id=student.id,status='present').count()
        relevant=Lecture.query.filter_by(class_name=student.class_name,division=student.division).count()
        return render_template('student_dashboard.html',student=student,lectures=lectures,present=total,total=relevant,percent=round(100*total/relevant) if relevant else 0)

    @app.get('/student/profile')
    @login_required('student')
    def student_profile():
        student=Student.query.filter_by(user_id=session['user_id']).first_or_404()
        return render_template('student_profile.html',student=student)

    @app.route('/student/face-registration', methods=['GET','POST'])
    @login_required('student')
    def face_registration():
        student=Student.query.filter_by(user_id=session['user_id']).first_or_404()
        if request.method=='POST':
            try:
                student.face_profile=encode_face(request.form.get('face_data',''))
                db.session.commit(); flash('Face profile saved. The captured photo itself was not stored.', 'success'); return redirect(url_for('student_profile'))
            except FaceError as exc: flash(str(exc),'error')
        return render_template('face_registration.html',student=student)

    @app.get('/student/lectures')
    @login_required('student')
    def student_lectures():
        student=Student.query.filter_by(user_id=session['user_id']).first_or_404()
        lectures=Lecture.query.filter_by(class_name=student.class_name,division=student.division).order_by(Lecture.lecture_date.desc(),Lecture.start_time).all()
        return render_template('student_lectures.html',lectures=lectures)

    @app.get('/student/attendance-history')
    @login_required('student')
    def attendance_history():
        student=Student.query.filter_by(user_id=session['user_id']).first_or_404()
        records=Attendance.query.filter_by(student_id=student.id).order_by(Attendance.marked_at.desc()).all()
        return render_template('attendance_history.html',records=records)

    @app.route('/attendance/mark/<int:lecture_id>', methods=['GET','POST'])
    @login_required('student')
    def mark_attendance(lecture_id):
        student=Student.query.filter_by(user_id=session['user_id']).first_or_404()
        lecture=Lecture.query.filter_by(id=lecture_id,class_name=student.class_name,division=student.division).first_or_404()
        result=None
        if request.method=='POST':
            lat=request.form.get('latitude',type=float); lon=request.form.get('longitude',type=float)
            campus = CampusSettings.query.first()
            policy = dict(app.config)
            if campus:
                policy.update(COLLEGE_LATITUDE=campus.latitude, COLLEGE_LONGITUDE=campus.longitude, GEOFENCE_RADIUS_METERS=campus.radius_meters)
            valid, reason, distance=check_attendance(lecture,student,lat,lon,policy)
            prior=Attendance.query.filter_by(lecture_id=lecture.id,student_id=student.id).first()
            if prior: valid,reason=False,'Duplicate attendance'
            face_ok=False
            if valid:
                if not student.face_profile: valid,reason=False,'Face profile not registered'
                else:
                    try: face_ok,_score=verify_face(student.face_profile,request.form.get('face_data',''),app.config['FACE_MATCH_THRESHOLD'])
                    except FaceError as exc: valid,reason=False,str(exc)
                    else:
                        if not face_ok: valid,reason=False,'Face verification failed'
            if not prior:
                record=Attendance(lecture_id=lecture.id,student_id=student.id,latitude=lat,longitude=lon,distance_from_campus=distance,face_verified=face_ok,status='present' if valid else 'rejected',rejection_reason=None if valid else reason)
                db.session.add(record)
                try: db.session.commit()
                except Exception:
                    db.session.rollback(); valid,reason=False,'Duplicate attendance'
            result={'approved':valid,'reason':'Attendance Approved' if valid else reason,'distance':distance}
            if valid: flash('Attendance approved.', 'success')
            else: flash(f'Attendance not approved: {reason}', 'error')
        return render_template('mark_attendance.html',lecture=lecture,student=student,result=result)

    @app.get('/api/campus-settings')
    @login_required('student')
    def campus_settings():
        setting=CampusSettings.query.first()
        return jsonify({'latitude':setting.latitude,'longitude':setting.longitude,'radius_meters':setting.radius_meters})

    @app.errorhandler(403)
    def forbidden(_): return render_template('error.html', code=403, message='You do not have permission to view this page.'),403
    @app.errorhandler(404)
    def missing(_): return render_template('error.html',code=404,message='The page or record was not found.'),404
    @app.errorhandler(413)
    def too_large(_): return render_template('error.html',code=413,message='The uploaded image is too large.'),413
    return app

app=create_app()
if __name__=='__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config.get('FLASK_DEBUG', '0') == '1')
