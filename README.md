# CampusFlow — Smart Attendance & Lecture Management

A local-first college demonstration project combining teacher-managed lecture scheduling, student dashboards, browser location checks, and an open-source face verification adapter. Python, Flask, SQLite, OpenCV, and browser APIs are free to run locally. The application does not call a paid map or AI service.

> **Academic demo limits:** Browser GPS coordinates can be spoofed, browser photos can be replayed, and the included OpenCV Haar detector plus image-similarity matcher is not a production-grade biometric identity system or liveness detector. Use fictional/demo records, obtain consent before biometric processing, and never use this prototype for consequential real-world decisions.

## Features

- Password hashing, Flask sessions, CSRF protection, and backend role enforcement.
- Teacher-only lecture creation/edit/cancel/delete, attendance review/correction, reporting, and audit records.
- Student-only class/division lecture visibility, face registration, attendance history, and check-in.
- Server-side lecture status, date/time window, class/division, geofence, face, and duplicate checks.
- Unique `(lecture_id, student_id)` attendance constraint; failed attempts are recorded with a reason.
- SQLite database created automatically on first start; `database/schema.sql` documents the tables.
- Responsive interface; no maps or paid APIs.

## Technology

Python 3.10–3.12, Flask, Flask-SQLAlchemy, Flask-WTF, SQLite, OpenCV, NumPy, browser Geolocation API, and `getUserMedia` camera access. SQLAlchemy models keep database access structured; a future MySQL Community Edition migration can use an appropriate free SQLAlchemy driver and `DATABASE_URL`.

## Folder structure

```text
smart-attendance/
├── app.py                    # Models, routes, auth, permissions, app factory
├── config.py                 # Environment-based app and campus settings
├── seed_demo.py              # Fictional demo accounts and sample lectures
├── create_teacher.py         # Interactive teacher account setup for hosting
├── wsgi.py                   # WSGI entry point for Python web hosts
├── requirements.txt
├── .env.example
├── README.md
├── database/schema.sql       # Reference schema
├── services/
│   ├── attendance_service.py # Time, lecture, class and geofence decisions
│   ├── face_service.py       # Local OpenCV face crop and matching adapter
│   └── geofence_service.py   # Haversine distance calculation
├── templates/                # Jinja pages for both roles and workflows
├── static/css/style.css      # Responsive visual design
├── static/js/                # Camera and location interaction
├── instance/                 # SQLite database (created automatically)
└── uploads/faces/            # Reserved private local storage; raw images aren't saved
```

## Install and run on Windows

1. Install Python 3.10, 3.11, or 3.12 from [python.org](https://www.python.org/downloads/). During setup, select **Add Python to PATH**.
2. Open PowerShell and move into this folder:

   ```powershell
   cd path\to\smart-attendance
   ```

3. Create and activate a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. Alternatively run `.venv\Scripts\python.exe` directly for each command.

4. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   OpenCV's prebuilt Python wheels normally install on Windows without a separate compiler. If your Python version has no compatible wheel, use Python 3.11 in a fresh environment. The headless wheel is sufficient because camera capture happens in the browser.

5. Create local configuration:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` and replace `SECRET_KEY` with a long random value. Set campus latitude, longitude, and radius to a location you control or use the demo defaults. Never commit your real `.env` file.

6. Create fictional demo accounts and schedules:

   ```powershell
   python seed_demo.py
   ```

   The SQLite database and tables are created automatically by this command. To start with a clean demo database, stop the server and remove `instance\attendance.db`, then run this command again.

7. Start the Flask server (exact command):

   ```powershell
   python app.py
   ```

8. Open `http://127.0.0.1:5000` in a current browser. Camera and GPS work on `localhost`/`127.0.0.1`; for a remote host browsers require HTTPS.

## Demo logins

These fictional credentials are created by `seed_demo.py`:

| Role | Username | Password |
|---|---|---|
| Teacher | `teacher.demo` | `TeachDemo123!` |
| Student | `student.asha` | `Student123!` |
| Student | `student.kabir` | `Student123!` |

Change demo passwords before showing the app on a shared machine. New student self-registration is also available. Teacher self-registration is intentionally disabled; the demo seed creates the teacher.

## Demo walkthrough

### Teacher

1. Sign in with the teacher credentials above.
2. Open **Lectures → Create lecture**.
3. Select a subject, date, start/end time, and an attendance window contained within the lecture; add a room if desired.
4. From the lecture list, edit or cancel a lecture. Deletion is available if no check-ins exist; otherwise the app cancels it to preserve history.
5. Open a lecture's attendance view to see approved/rejected attempts, distance, and reason. The teacher can correct a record; each correction is audited.
6. Use **Reports** to filter recorded attempts by date, class, division, or student.

### Student and face registration

1. Sign in as a student or register a new student with a matching class/division.
2. Open **My profile → Register face**, choose **Enable camera**, center one face in good light, then choose **Capture face** and **Save face profile**.
3. The browser sends the captured frame to the local Flask app. OpenCV detects one face, makes a normalized grayscale crop, and stores only that compact representation in SQLite. No raw face image file is written.
4. A successful registration is required before marking attendance.

### Mark attendance

1. Create a lecture for today's date with the attendance window open now. Use the demo class `FYCS`, division `A`.
2. Sign in as a registered demo student and choose **Mark attendance** on the lecture.
3. The browser requests GPS and camera permission. The server checks lecture status, date/time, class/division, campus distance, face match, and duplicate attendance before approving.
4. A success or precise rejection reason is shown. A repeat attempt is rejected as a duplicate.

## Geofencing and time checks

Teachers can set the campus center and radius from **Teacher Dashboard → Campus location**. Find the college in Google Maps or OpenStreetMap, right-click the campus center, then enter the displayed coordinates in latitude-first order. Choose a radius in meters (for example, 100–300 m for a demo campus). Changes save to SQLite and apply to the next attendance check immediately. The application computes great-circle distance with the Haversine formula and makes no map request. Browser coordinates aren't tamper-proof.

Attendance is date-bound and accepted only between the lecture's configured opening and closing times. To demonstrate rejection, attempt before the opening time, after closing, or on a different date. The server clock is authoritative.

## Share online with students (free demo hosting)

For a college demo that students can open from anywhere, the site needs a public HTTPS address. PythonAnywhere currently offers a limited free web-app account with a `yourusername.pythonanywhere.com` address and SSL support. Free accounts have usage and account-retention limits, so treat this as a demonstration host. Render also offers free Python services, but its free filesystem is temporary: a local SQLite database can be lost on restart, redeploy, or spin-down. Check the provider's current free-tier limits before choosing.

### PythonAnywhere outline

1. Create your own free PythonAnywhere account and create one Flask web app. The account and any provider verification stay under your control.
2. Upload the deployment ZIP for this project and extract it under `/home/YOURUSERNAME/smart-attendance` using the provider's file console.
3. Create a virtual environment from a PythonAnywhere Bash console and install packages:

   ```bash
   python3.11 -m venv ~/.virtualenvs/campusflow
   ~/.virtualenvs/campusflow/bin/pip install -r ~/smart-attendance/requirements.txt
   ```

4. Set the Web tab's virtualenv path to `/home/YOURUSERNAME/.virtualenvs/campusflow`.
5. In the WSGI configuration file shown by the Web tab, set the project path and import the app:

   ```python
   import sys
   project = '/home/YOURUSERNAME/smart-attendance'
   if project not in sys.path:
       sys.path.insert(0, project)
   from app import app as application
   ```

6. Create a private `.env` in the project folder (never add it to the ZIP or GitHub). Set `APP_ENV=production`, a long random `SECRET_KEY`, the campus latitude/longitude, geofence radius, and `DATABASE_URL=sqlite:////home/YOURUSERNAME/smart-attendance/instance/attendance.db`.
7. From the console, create a teacher account without putting its password in a command or chat:

   ```bash
   cd ~/smart-attendance
   ~/.virtualenvs/campusflow/bin/python create_teacher.py
   ```

8. In the Web tab, click **Reload**, then open the HTTPS site URL on a phone. Confirm HTTPS is active before students register face profiles or use GPS/camera check-in.
9. Share the HTTPS link with students. They create student accounts on the register page; access and profiles then live on the hosted server.

The public host stores account records, attendance data, and compact face representations. For an academic demo, use student consent and fictional accounts unless your college has approved real biometric attendance. This project does not provide production-grade face liveness or anti-spoofing.
## Roles and security notes

- Teacher routes enforce a teacher session and scope lecture reads/changes to that teacher's owned record.
- Students can see only lectures matching their class/division. Student routes do not accept attendance status changes.
- Failed verification attempts are recorded; each lecture/student pair can have only one attempt. This makes duplicate prevention clear, but a failed attempt also consumes the unique pair in this demo.
- All state-changing forms use CSRF tokens. SQLAlchemy parameterizes database operations, and passwords use Werkzeug's password hashing.
- Face vectors are sensitive personal data even without the source photo. Keep the SQLite file private and clear demo records after class.

## Troubleshooting

- **`python` or `py` not found:** reinstall Python and enable PATH, or reopen PowerShell after installation.
- **OpenCV install fails:** use 64-bit Python 3.11 and recreate `.venv`, then run `pip install -r requirements.txt` again.
- **Camera/GPS unavailable:** use a recent browser on `http://127.0.0.1:5000`, allow permissions, and check Windows privacy settings. Remote access needs HTTPS.
- **No face detected:** improve lighting, face the camera, remove other people from frame, and capture again.
- **Face mismatch:** re-register the face under the same student account and use similar lighting/position. The demo matcher is intentionally simple.
- **Outside campus:** update the sample `.env` coordinates and radius, then restart Flask. The campus row is seeded at first DB creation; if changing settings after that, edit the `campus_settings` row or rebuild the demo DB.
- **No subject appears for teacher:** rerun `python seed_demo.py` only if demo teacher isn't already present; add subjects via the database/admin extension in a future iteration. Demo seed is idempotent.
- **403 page:** sign in using the correct role; backend role checks intentionally deny cross-role access.
- **CSRF error:** load the page again and submit its current form; avoid stale tabs after restarting the server.

## Viva/demo summary

The project separates routes, data models, and verification services. SQLAlchemy creates foreign keys and the unique attendance constraint. The browser collects camera and location inputs, but authorization, lecture/window/class checks, distance calculation, face matching, and duplicate checks execute in Flask. This demonstrates a full-stack flow while keeping every external service optional and free.
