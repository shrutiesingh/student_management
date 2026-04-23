from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    UserProfile, Department, Course, AcademicYear, Semester,
    Subject, Teacher, Student, Attendance, ExamType, Marks, Notice
)


# ──────────────────────────────────────────────────────
#  HELPER: get role of logged-in user
# ──────────────────────────────────────────────────────
def get_role(user):
    try:
        return user.profile.role
    except Exception:
        return 'student'


# ──────────────────────────────────────────────────────
#  AUTH VIEWS
# ──────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'sms/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ──────────────────────────────────────────────────────
#  DASHBOARD  (role-based)
# ──────────────────────────────────────────────────────
@login_required
def dashboard(request):
    role  = get_role(request.user)
    ctx   = {'role': role}
    notices = Notice.objects.filter(is_active=True)

    if role == 'admin' or request.user.is_superuser:
        ctx.update({
            'total_students':   Student.objects.filter(is_active=True).count(),
            'total_teachers':   Teacher.objects.count(),
            'total_courses':    Course.objects.count(),
            'total_subjects':   Subject.objects.count(),
            'recent_students':  Student.objects.order_by('-admission_date')[:5],
            'notices':          notices.filter(audience__in=['all']),
        })
        return render(request, 'sms/dashboard_admin.html', ctx)

    elif role == 'teacher':
        teacher = get_object_or_404(Teacher, user=request.user)
        my_subjects = teacher.subjects.all()
        today = date.today()
        today_attendance_count = Attendance.objects.filter(
            subject__in=my_subjects, date=today).count()
        ctx.update({
            'teacher': teacher,
            'my_subjects': my_subjects,
            'today_attendance': today_attendance_count,
            'notices': notices.filter(audience__in=['all', 'teacher']),
            'recent_marks': Marks.objects.filter(entered_by=teacher).order_by('-entered_at')[:8],
        })
        return render(request, 'sms/dashboard_teacher.html', ctx)

    else:  # student
        student = get_object_or_404(Student, user=request.user)
        # Attendance summary
        my_att  = Attendance.objects.filter(student=student)
        present = my_att.filter(status='P').count()
        total   = my_att.count()
        att_pct = round((present / total * 100), 1) if total else 0

        # Latest marks
        latest_marks = Marks.objects.filter(student=student).order_by('-entered_at')[:10]

        ctx.update({
            'student': student,
            'attendance_pct': att_pct,
            'present': present,
            'total_classes': total,
            'latest_marks': latest_marks,
            'notices': notices.filter(audience__in=['all', 'student']),
        })
        return render(request, 'sms/dashboard_student.html', ctx)


# ──────────────────────────────────────────────────────
#  STUDENT MANAGEMENT  (admin / teacher)
# ──────────────────────────────────────────────────────
@login_required
def student_list(request):
    role = get_role(request.user)
    students = Student.objects.select_related('user', 'course', 'current_semester').filter(is_active=True)

    q = request.GET.get('q', '')
    course_id = request.GET.get('course', '')
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(enrollment_no__icontains=q)
        )
    if course_id:
        students = students.filter(course_id=course_id)

    return render(request, 'sms/student_list.html', {
        'students': students,
        'courses': Course.objects.all(),
        'q': q,
        'role': role,
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    role    = get_role(request.user)

    # Block student from viewing other students
    if role == 'student' and student.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    # Attendance per subject
    subjects = []
    if student.current_semester:
        for subj in student.current_semester.subjects.all():
            att  = Attendance.objects.filter(student=student, subject=subj)
            tot  = att.count()
            pres = att.filter(status='P').count()
            subjects.append({
                'subject': subj,
                'total': tot,
                'present': pres,
                'pct': round(pres/tot*100, 1) if tot else 0,
            })

    # Marks per semester
    marks_qs = Marks.objects.filter(student=student).select_related('subject', 'exam_type', 'semester')

    return render(request, 'sms/student_detail.html', {
        'student': student,
        'subjects': subjects,
        'marks': marks_qs,
        'role': role,
    })


@login_required
def student_add(request):
    if get_role(request.user) not in ('admin',) and not request.user.is_superuser:
        messages.error(request, "Only admins can add students.")
        return redirect('dashboard')

    courses   = Course.objects.all()
    semesters = Semester.objects.all()

    if request.method == 'POST':
        p = request.POST
        # Create Django User
        user = User.objects.create_user(
            username   = p['enrollment_no'],
            password   = p['password'],
            first_name = p['first_name'],
            last_name  = p['last_name'],
            email      = p['email'],
        )
        UserProfile.objects.create(user=user, role='student')

        semester_obj = None
        if p.get('current_semester'):
            semester_obj = Semester.objects.get(pk=p['current_semester'])

        Student.objects.create(
            user=user,
            enrollment_no   = p['enrollment_no'],
            course          = Course.objects.get(pk=p['course']),
            current_semester = semester_obj,
            date_of_birth   = p['date_of_birth'],
            gender          = p['gender'],
            blood_group     = p.get('blood_group', ''),
            mobile          = p['mobile'],
            email           = p['email'],
            address         = p['address'],
            city            = p['city'],
            state           = p['state'],
            pincode         = p['pincode'],
            father_name     = p['father_name'],
            father_mobile   = p['father_mobile'],
            father_occupation = p.get('father_occupation', ''),
            mother_name     = p['mother_name'],
            mother_mobile   = p.get('mother_mobile', ''),
            guardian_name   = p.get('guardian_name', ''),
            guardian_mobile = p.get('guardian_mobile', ''),
            guardian_relation = p.get('guardian_relation', ''),
        )
        messages.success(request, f"Student {p['first_name']} added successfully!")
        return redirect('student_list')

    return render(request, 'sms/student_form.html', {
        'courses': courses,
        'semesters': semesters,
        'action': 'Add',
    })


@login_required
def student_edit(request, pk):
    if get_role(request.user) not in ('admin',) and not request.user.is_superuser:
        messages.error(request, "Only admins can edit students.")
        return redirect('dashboard')

    student   = get_object_or_404(Student, pk=pk)
    courses   = Course.objects.all()
    semesters = Semester.objects.all()

    if request.method == 'POST':
        p = request.POST
        u = student.user
        u.first_name = p['first_name']
        u.last_name  = p['last_name']
        u.email      = p['email']
        if p.get('password'):
            u.set_password(p['password'])
        u.save()

        student.course          = Course.objects.get(pk=p['course'])
        student.current_semester = Semester.objects.get(pk=p['current_semester']) if p.get('current_semester') else None
        student.date_of_birth   = p['date_of_birth']
        student.gender          = p['gender']
        student.blood_group     = p.get('blood_group', '')
        student.mobile          = p['mobile']
        student.email           = p['email']
        student.address         = p['address']
        student.city            = p['city']
        student.state           = p['state']
        student.pincode         = p['pincode']
        student.father_name     = p['father_name']
        student.father_mobile   = p['father_mobile']
        student.father_occupation = p.get('father_occupation', '')
        student.mother_name     = p['mother_name']
        student.mother_mobile   = p.get('mother_mobile', '')
        student.guardian_name   = p.get('guardian_name', '')
        student.guardian_mobile = p.get('guardian_mobile', '')
        student.guardian_relation = p.get('guardian_relation', '')
        student.save()

        messages.success(request, "Student updated successfully!")
        return redirect('student_detail', pk=student.pk)

    return render(request, 'sms/student_form.html', {
        'student': student,
        'courses': courses,
        'semesters': semesters,
        'action': 'Edit',
    })


# ──────────────────────────────────────────────────────
#  ATTENDANCE  VIEWS
# ──────────────────────────────────────────────────────
@login_required
def attendance_mark(request):
    role = get_role(request.user)
    if role not in ('teacher', 'admin') and not request.user.is_superuser:
        messages.error(request, "Only teachers can mark attendance.")
        return redirect('dashboard')

    subjects  = Subject.objects.all()
    if role == 'teacher':
        teacher  = get_object_or_404(Teacher, user=request.user)
        subjects = teacher.subjects.all()

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        att_date   = request.POST.get('date')
        subject    = get_object_or_404(Subject, pk=subject_id)
        teacher_obj = None
        if role == 'teacher':
            teacher_obj = get_object_or_404(Teacher, user=request.user)

        # Get all students in this subject's semester
        students = Student.objects.filter(current_semester=subject.semester, is_active=True)
        for student in students:
            status = request.POST.get(f'status_{student.pk}', 'A')
            Attendance.objects.update_or_create(
                student=student, subject=subject, date=att_date,
                defaults={'status': status, 'marked_by': teacher_obj}
            )
        messages.success(request, f"Attendance marked for {students.count()} students!")
        return redirect('attendance_mark')

    return render(request, 'sms/attendance_mark.html', {
        'subjects': subjects,
        'today': date.today(),
    })


@login_required
def attendance_view(request):
    """View attendance - students see own, teachers see their subjects."""
    role = get_role(request.user)

    if role == 'student':
        student = get_object_or_404(Student, user=request.user)
        records = Attendance.objects.filter(student=student).select_related('subject').order_by('-date')
        # Summary per subject
        summary = {}
        for r in records:
            k = r.subject.name
            if k not in summary:
                summary[k] = {'total': 0, 'present': 0}
            summary[k]['total'] += 1
            if r.status == 'P':
                summary[k]['present'] += 1
        for k in summary:
            t = summary[k]['total']
            p = summary[k]['present']
            summary[k]['pct'] = round(p/t*100, 1) if t else 0

        return render(request, 'sms/attendance_student.html', {
            'records': records[:50],
            'summary': summary,
            'student': student,
        })

    # Teacher / Admin view
    subjects = Subject.objects.all()
    if role == 'teacher':
        teacher  = get_object_or_404(Teacher, user=request.user)
        subjects = teacher.subjects.all()

    subject_id = request.GET.get('subject')
    att_date   = request.GET.get('date', str(date.today()))
    records    = []
    sel_subject = None

    if subject_id:
        sel_subject = get_object_or_404(Subject, pk=subject_id)
        records = Attendance.objects.filter(
            subject=sel_subject, date=att_date
        ).select_related('student__user')

    return render(request, 'sms/attendance_teacher.html', {
        'subjects': subjects,
        'records': records,
        'sel_subject': sel_subject,
        'att_date': att_date,
        'role': role,
    })


# ──────────────────────────────────────────────────────
#  MARKS / RESULT  VIEWS
# ──────────────────────────────────────────────────────
@login_required
def marks_entry(request):
    role = get_role(request.user)
    if role not in ('teacher', 'admin') and not request.user.is_superuser:
        messages.error(request, "Only teachers can enter marks.")
        return redirect('dashboard')

    subjects   = Subject.objects.all()
    exam_types = ExamType.objects.all()
    if role == 'teacher':
        teacher  = get_object_or_404(Teacher, user=request.user)
        subjects = teacher.subjects.all()

    if request.method == 'POST':
        subject_id   = request.POST.get('subject')
        exam_type_id = request.POST.get('exam_type')
        semester_id  = request.POST.get('semester')
        subject      = get_object_or_404(Subject, pk=subject_id)
        exam_type    = get_object_or_404(ExamType, pk=exam_type_id)
        semester     = get_object_or_404(Semester, pk=semester_id)
        teacher_obj  = get_object_or_404(Teacher, user=request.user) if role == 'teacher' else None

        students = Student.objects.filter(current_semester=semester, is_active=True)
        count = 0
        for student in students:
            obtained = request.POST.get(f'marks_{student.pk}')
            if obtained is not None and obtained != '':
                Marks.objects.update_or_create(
                    student=student, subject=subject,
                    exam_type=exam_type, semester=semester,
                    defaults={'obtained': obtained, 'entered_by': teacher_obj}
                )
                count += 1
        messages.success(request, f"Marks saved for {count} students!")
        return redirect('marks_entry')

    return render(request, 'sms/marks_entry.html', {
        'subjects':   subjects,
        'exam_types': exam_types,
        'semesters':  Semester.objects.all(),
    })


@login_required
def result_view(request):
    """Student sees own result; teacher/admin can search any student."""
    role = get_role(request.user)

    if role == 'student':
        student  = get_object_or_404(Student, user=request.user)
        return _render_result(request, student)

    # Admin / teacher – search
    students = Student.objects.filter(is_active=True).select_related('user')
    q = request.GET.get('q', '')
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q)|Q(user__last_name__icontains=q)|
            Q(enrollment_no__icontains=q)
        )
    student_id = request.GET.get('student_id')
    if student_id:
        student = get_object_or_404(Student, pk=student_id)
        return _render_result(request, student, role=role)

    return render(request, 'sms/result_search.html', {
        'students': students, 'q': q, 'role': role
    })


def _render_result(request, student, role='student'):
    marks_qs = Marks.objects.filter(student=student).select_related(
        'subject', 'exam_type', 'semester'
    ).order_by('semester__number', 'subject__name')

    # Group by semester
    semesters_data = {}
    for m in marks_qs:
        sem_key = f"Semester {m.semester.number}"
        if sem_key not in semesters_data:
            semesters_data[sem_key] = {'marks': [], 'total': 0, 'obtained': 0}
        semesters_data[sem_key]['marks'].append(m)
        semesters_data[sem_key]['total']    += m.exam_type.max_marks
        semesters_data[sem_key]['obtained'] += float(m.obtained)

    for k in semesters_data:
        t = semesters_data[k]['total']
        o = semesters_data[k]['obtained']
        semesters_data[k]['pct'] = round(o/t*100, 1) if t else 0

    return render(request, 'sms/result_detail.html', {
        'student': student,
        'semesters_data': semesters_data,
        'role': role,
    })


# ──────────────────────────────────────────────────────
#  TEACHER VIEWS
# ──────────────────────────────────────────────────────
@login_required
def teacher_list(request):
    teachers = Teacher.objects.select_related('user', 'department').all()
    return render(request, 'sms/teacher_list.html', {'teachers': teachers, 'role': get_role(request.user)})


@login_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'sms/teacher_detail.html', {'teacher': teacher, 'role': get_role(request.user)})


# ──────────────────────────────────────────────────────
#  NOTICE BOARD
# ──────────────────────────────────────────────────────
@login_required
def notice_list(request):
    role = get_role(request.user)
    notices = Notice.objects.filter(is_active=True)
    if role == 'student':
        notices = notices.filter(audience__in=['all', 'student'])
    elif role == 'teacher':
        notices = notices.filter(audience__in=['all', 'teacher'])

    return render(request, 'sms/notice_list.html', {'notices': notices, 'role': role})


@login_required
def notice_add(request):
    if get_role(request.user) not in ('admin', 'teacher') and not request.user.is_superuser:
        return redirect('dashboard')
    if request.method == 'POST':
        Notice.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            audience=request.POST['audience'],
            created_by=request.user,
        )
        messages.success(request, "Notice posted!")
        return redirect('notice_list')
    return render(request, 'sms/notice_form.html')


# ──────────────────────────────────────────────────────
#  AJAX: Load students for a subject/semester
# ──────────────────────────────────────────────────────
@login_required
def ajax_students_for_subject(request):
    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'students': []})
    subject  = get_object_or_404(Subject, pk=subject_id)
    students = Student.objects.filter(current_semester=subject.semester, is_active=True).select_related('user')
    data = [{'id': s.pk, 'name': s.user.get_full_name(), 'enrollment': s.enrollment_no} for s in students]
    return JsonResponse({'students': data})


@login_required
def ajax_semesters_for_subject(request):
    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'semester_id': None})
    subject = get_object_or_404(Subject, pk=subject_id)
    return JsonResponse({'semester_id': subject.semester.pk, 'semester_name': str(subject.semester)})


# ──────────────────────────────────────────────────────
#  MY PROFILE
# ──────────────────────────────────────────────────────
@login_required
def my_profile(request):
    role = get_role(request.user)
    ctx  = {'role': role}
    if role == 'student':
        ctx['student'] = get_object_or_404(Student, user=request.user)
    elif role == 'teacher':
        ctx['teacher'] = get_object_or_404(Teacher, user=request.user)
    return render(request, 'sms/profile.html', ctx)
