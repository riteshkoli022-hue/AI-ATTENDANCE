"""Create a real teacher account locally or from a hosting provider's console."""
from getpass import getpass
from app import create_app, db, User, Teacher
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    username = input('Teacher username: ').strip().lower()
    name = input('Teacher full name: ').strip()
    department = input('Department: ').strip()
    password = getpass('Password (12+ characters): ')
    confirmation = getpass('Confirm password: ')
    if len(password) < 12 or password != confirmation:
        raise SystemExit('Password must be at least 12 characters and both entries must match.')
    if not username or not name or not department:
        raise SystemExit('Username, name, and department are required.')
    if User.query.filter_by(username=username).first():
        raise SystemExit('That username already exists.')
    user = User(username=username, password_hash=generate_password_hash(password), role='teacher')
    db.session.add(user)
    db.session.flush()
    db.session.add(Teacher(user_id=user.id, teacher_name=name, department=department))
    db.session.commit()
    print('Teacher account created.')
