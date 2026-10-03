from datetime import datetime
from services.geofence_service import inside_geofence

def check_attendance(lecture, student, lat, lon, config, now=None):
    now = now or datetime.now()
    if lecture.status != "active":
        return False, "Lecture inactive", None
    if now.date().isoformat() != lecture.lecture_date:
        return False, "Lecture is not scheduled for today", None
    opens = datetime.combine(now.date(), datetime.strptime(lecture.attendance_open_time, "%H:%M").time())
    closes = datetime.combine(now.date(), datetime.strptime(lecture.attendance_close_time, "%H:%M").time())
    if now < opens or now > closes:
        return False, "Outside time window", None
    if student.class_name != lecture.class_name or student.division != lecture.division:
        return False, "Unauthorized class/division", None
    try:
        inside, distance = inside_geofence(lat, lon, config["COLLEGE_LATITUDE"], config["COLLEGE_LONGITUDE"], config["GEOFENCE_RADIUS_METERS"])
    except (TypeError, ValueError):
        return False, "Location unavailable or invalid", None
    if not inside:
        return False, "Outside campus", distance
    return True, "Checks passed", distance
