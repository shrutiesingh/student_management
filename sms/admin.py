from django.contrib import admin
from .models import (
    UserProfile, Department, Course, AcademicYear, Semester,
    Subject, Teacher, Student, Attendance, ExamType, Marks, Notice
)

admin.site.site_header  = "SMS Admin Panel"
admin.site.site_title   = "Student Management"
admin.site.index_title  = "Welcome to SMS Administration"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter  = ['role']

@admin.register(Department)
class DeptAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'duration_years']

@admin.register(AcademicYear)
class AcYearAdmin(admin.ModelAdmin):
    list_display = ['year_label', 'is_current', 'start_date', 'end_date']

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'number', 'course', 'academic_year']
    list_filter  = ['course', 'academic_year']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'semester', 'credits']
    list_filter  = ['semester__course']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display  = ['__str__', 'employee_id', 'department', 'designation']
    filter_horizontal = ['subjects']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ['enrollment_no', '__str__', 'course', 'current_semester', 'is_active']
    list_filter   = ['course', 'is_active', 'gender']
    search_fields = ['enrollment_no', 'user__first_name', 'user__last_name']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'status']
    list_filter  = ['status', 'date', 'subject']

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_marks', 'pass_marks']

@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'obtained', 'semester']
    list_filter  = ['exam_type', 'semester']

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'created_by', 'created_at', 'is_active']
