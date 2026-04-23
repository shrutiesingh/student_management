from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',         views.login_view,  name='login'),
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Students
    path('students/',              views.student_list,   name='student_list'),
    path('students/add/',          views.student_add,    name='student_add'),
    path('students/<int:pk>/',     views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/',views.student_edit,   name='student_edit'),

    # Teachers
    path('teachers/',           views.teacher_list,   name='teacher_list'),
    path('teachers/<int:pk>/',  views.teacher_detail, name='teacher_detail'),

    # Attendance
    path('attendance/mark/',    views.attendance_mark, name='attendance_mark'),
    path('attendance/view/',    views.attendance_view, name='attendance_view'),

    # Marks / Result
    path('marks/entry/',        views.marks_entry,  name='marks_entry'),
    path('result/',             views.result_view,  name='result_view'),

    # Notices
    path('notices/',            views.notice_list,  name='notice_list'),
    path('notices/add/',        views.notice_add,   name='notice_add'),

    # Profile
    path('profile/',            views.my_profile,   name='my_profile'),

    # AJAX
    path('ajax/students-for-subject/', views.ajax_students_for_subject, name='ajax_students_for_subject'),
    path('ajax/semester-for-subject/', views.ajax_semesters_for_subject, name='ajax_semesters_for_subject'),
]
