"""
seed_data.py  –  Run once to populate the database with sample data.
Usage:  python manage.py shell < seed_data.py
  OR :  python seed_data.py  (from project root after activating venv)
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date, timedelta
from django.contrib.auth.models import User
from sms.models import (
    UserProfile, Department, Course, AcademicYear,
    Semester, Subject, Teacher, Student, ExamType, Notice
)

print("🌱 Seeding database...")

# ── SUPERUSER ──
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@college.edu', 'admin123')
    admin.first_name = 'Super'; admin.last_name = 'Admin'; admin.save()
    UserProfile.objects.create(user=admin, role='admin')
    print("  ✓ Admin user created  (username: admin / password: admin123)")

# ── DEPARTMENTS ──
cs_dept, _ = Department.objects.get_or_create(name='Computer Science', code='CS')
ec_dept, _ = Department.objects.get_or_create(name='Electronics', code='EC')
print("  ✓ Departments created")

# ── COURSES ──
btech_cs, _ = Course.objects.get_or_create(
    code='BTECH-CS',
    defaults={'name': 'B.Tech Computer Science', 'department': cs_dept, 'duration_years': 4}
)
btech_ec, _ = Course.objects.get_or_create(
    code='BTECH-EC',
    defaults={'name': 'B.Tech Electronics', 'department': ec_dept, 'duration_years': 4}
)
print("  ✓ Courses created")

# ── ACADEMIC YEAR ──
ay, _ = AcademicYear.objects.get_or_create(
    year_label='2024-25',
    defaults={'is_current': True, 'start_date': date(2024, 7, 1), 'end_date': date(2025, 6, 30)}
)
print("  ✓ Academic year created")

# ── SEMESTERS ──
sems = {}
for i in range(1, 9):
    sem, _ = Semester.objects.get_or_create(
        course=btech_cs, number=i, academic_year=ay,
        defaults={
            'start_date': date(2024, 7, 1) + timedelta(days=(i-1)*180),
            'end_date':   date(2024, 7, 1) + timedelta(days=i*180)
        }
    )
    sems[i] = sem
print("  ✓ Semesters created")

# ── SUBJECTS (Semester 1 & 2) ──
subj_data = [
    ('Mathematics I',      'MATH101', 1, 4),
    ('Physics',            'PHY101',  1, 4),
    ('C Programming',      'CS101',   1, 4),
    ('Engineering Drawing','ED101',   1, 2),
    ('Mathematics II',     'MATH201', 2, 4),
    ('Data Structures',    'CS201',   2, 4),
    ('Digital Electronics','CS202',   2, 4),
    ('OOP with Java',      'CS203',   2, 4),
    ('DBMS',               'CS301',   3, 4),
    ('Operating Systems',  'CS302',   3, 4),
    ('Computer Networks',  'CS303',   3, 4),
]
subjects = {}
for name, code, sem_no, credits in subj_data:
    subj, _ = Subject.objects.get_or_create(
        code=code,
        defaults={'name': name, 'semester': sems[sem_no], 'credits': credits}
    )
    subjects[code] = subj
print("  ✓ Subjects created")

# ── TEACHERS ──
teacher_data = [
    ('teacher1', 'Rajesh', 'Kumar',   'teacher1@college.edu', 'T001', 'Associate Professor', '9876543001'),
    ('teacher2', 'Priya',  'Sharma',  'teacher2@college.edu', 'T002', 'Assistant Professor', '9876543002'),
    ('teacher3', 'Amit',   'Verma',   'teacher3@college.edu', 'T003', 'Professor',            '9876543003'),
]
for uname, fname, lname, email, emp_id, desig, mobile in teacher_data:
    if not User.objects.filter(username=uname).exists():
        u = User.objects.create_user(uname, email, 'teacher123',
                                     first_name=fname, last_name=lname)
        UserProfile.objects.create(user=u, role='teacher')
        t = Teacher.objects.create(
            user=u, employee_id=emp_id, department=cs_dept,
            designation=desig, mobile=mobile,
            address='123 Faculty Quarters, College Campus',
            joining_date=date(2020, 7, 1)
        )
        # Assign subjects
        t.subjects.add(*list(subjects.values())[:4])

print("  ✓ Teachers created  (password: teacher123)")

# ── STUDENTS ──
student_data = [
    ('2024CS001', 'Arjun',   'Singh',  '2024cs001@student.edu', '9111111001', 'M', date(2005, 3, 15)),
    ('2024CS002', 'Neha',    'Gupta',  '2024cs002@student.edu', '9111111002', 'F', date(2005, 7, 22)),
    ('2024CS003', 'Rohan',   'Patel',  '2024cs003@student.edu', '9111111003', 'M', date(2005, 1, 10)),
    ('2024CS004', 'Ananya',  'Mishra', '2024cs004@student.edu', '9111111004', 'F', date(2005, 11, 5)),
    ('2024CS005', 'Vikram',  'Yadav',  '2024cs005@student.edu', '9111111005', 'M', date(2005, 6, 30)),
    ('2023CS001', 'Deepika', 'Nair',   '2023cs001@student.edu', '9111111006', 'F', date(2004, 4, 18)),
]
for enrollment, fname, lname, email, mobile, gender, dob in student_data:
    if not User.objects.filter(username=enrollment).exists():
        u = User.objects.create_user(enrollment, email, 'student123',
                                     first_name=fname, last_name=lname)
        UserProfile.objects.create(user=u, role='student')
        sem = sems[1] if enrollment.startswith('2024') else sems[3]
        Student.objects.create(
            user=u,
            enrollment_no=enrollment,
            course=btech_cs,
            current_semester=sem,
            date_of_birth=dob,
            gender=gender,
            blood_group='O+',
            mobile=mobile,
            email=email,
            address='456 Student Housing, College Road',
            city='Jaipur',
            state='Rajasthan',
            pincode='302001',
            father_name=f'{fname} Father',
            father_mobile='9888888001',
            father_occupation='Business',
            mother_name=f'{fname} Mother',
            mother_mobile='9888888002',
        )
print("  ✓ Students created  (password: student123)")

# ── EXAM TYPES ──
ExamType.objects.get_or_create(name='Mid-Term',  defaults={'max_marks': 30,  'pass_marks': 12})
ExamType.objects.get_or_create(name='End-Term',  defaults={'max_marks': 70,  'pass_marks': 28})
ExamType.objects.get_or_create(name='Internal',  defaults={'max_marks': 20,  'pass_marks': 8})
ExamType.objects.get_or_create(name='Practical', defaults={'max_marks': 50,  'pass_marks': 20})
print("  ✓ Exam types created")

# ── NOTICES ──
admin_user = User.objects.get(username='admin')
Notice.objects.get_or_create(
    title='Welcome to EduPro SMS!',
    defaults={
        'content': 'Welcome to our new Student Management System. Please update your profile and check your timetable.',
        'audience': 'all',
        'created_by': admin_user,
    }
)
Notice.objects.get_or_create(
    title='Mid-Term Examination Schedule Released',
    defaults={
        'content': 'The Mid-Term examination schedule has been released. Exams begin from next Monday. Students are advised to prepare accordingly.',
        'audience': 'student',
        'created_by': admin_user,
    }
)
Notice.objects.get_or_create(
    title='Faculty Meeting – 15th of this month',
    defaults={
        'content': 'All faculty members are requested to attend the mandatory faculty meeting in the conference hall.',
        'audience': 'teacher',
        'created_by': admin_user,
    }
)
print("  ✓ Sample notices created")

print("\n✅  Seeding complete!")
print("─" * 50)
print("  🔑 Login Credentials:")
print("  Admin   → username: admin     | password: admin123")
print("  Teacher → username: teacher1  | password: teacher123")
print("  Student → username: 2024CS001 | password: student123")
print("─" * 50)
print("  🚀 Run: python manage.py runserver")
print("  🌐 Open: http://127.0.0.1:8000/")
