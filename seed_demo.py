"""Create or repair the fictional demo accounts, subjects, and lectures."""

from app import create_app, seed_demo_data

app = create_app()
with app.app_context():
    seed_demo_data()
    print("Demo accounts are ready. Teacher: teacher.demo / TeachDemo123!")
    print("Students: student.asha and student.kabir / Student123!")
