from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# ─────────────────────────────────────────────
#  ROLE PROFILE  (extends Django's built-in User)
# ─────────────────────────────────────────────
class UserProfile(models.Model):
    """
    Links Django's User to either a Student or Teacher profile.
    role = 'student' | 'teacher' | 'admin'
    """
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    user   = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role   = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    photo  = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"


# ─────────────────────────────────────────────
#  DEPARTMENT  &  COURSE
# ─────────────────────────────────────────────
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name       = models.CharField(max_length=200)
    code       = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    duration_years = models.PositiveSmallIntegerField(default=4)

    def __str__(self):
        return f"{self.code} – {self.name}"

    @property
    def total_semesters(self):
        return self.duration_years * 2


# ─────────────────────────────────────────────
#  ACADEMIC YEAR  &  SEMESTER
# ─────────────────────────────────────────────
class AcademicYear(models.Model):
    year_label  = models.CharField(max_length=20, unique=True)   # e.g. "2023-24"
    is_current  = models.BooleanField(default=False)
    start_date  = models.DateField()
    end_date    = models.DateField()

    def __str__(self):
        return self.year_label

    def save(self, *args, **kwargs):
        # Only one year can be current
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    course        = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    number        = models.PositiveSmallIntegerField()   # 1 – 8
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    start_date    = models.DateField()
    end_date      = models.DateField()

    class Meta:
        unique_together = ('course', 'number', 'academic_year')
        ordering = ['number']

    def __str__(self):
        return f"Sem {self.number} – {self.course.code} ({self.academic_year})"


# ─────────────────────────────────────────────
#  SUBJECT
# ─────────────────────────────────────────────
class Subject(models.Model):
    name     = models.CharField(max_length=200)
    code     = models.CharField(max_length=20, unique=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    credits  = models.PositiveSmallIntegerField(default=4)

    def __str__(self):
        return f"{self.code} – {self.name}"


# ─────────────────────────────────────────────
#  TEACHER
# ─────────────────────────────────────────────
class Teacher(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    employee_id = models.CharField(max_length=20, unique=True)
    department  = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='teachers')
    designation = models.CharField(max_length=100, default='Assistant Professor')
    mobile      = models.CharField(max_length=15)
    address     = models.TextField()
    subjects    = models.ManyToManyField(Subject, related_name='teachers', blank=True)
    joining_date = models.DateField()

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


# ─────────────────────────────────────────────
#  STUDENT  (complete personal info)
# ─────────────────────────────────────────────
class Student(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    GENDER_CHOICES = [('M','Male'),('F','Female'),('O','Other')]

    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    enrollment_no = models.CharField(max_length=20, unique=True)
    course        = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    current_semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)

    # Personal Info
    date_of_birth = models.DateField()
    gender        = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group   = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    mobile        = models.CharField(max_length=15)
    email         = models.EmailField()
    address       = models.TextField()
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100)
    pincode       = models.CharField(max_length=10)

    # Guardian Info
    father_name    = models.CharField(max_length=100)
    father_mobile  = models.CharField(max_length=15)
    father_occupation = models.CharField(max_length=100, blank=True)
    mother_name    = models.CharField(max_length=100)
    mother_mobile  = models.CharField(max_length=15, blank=True)
    guardian_name  = models.CharField(max_length=100, blank=True)
    guardian_mobile = models.CharField(max_length=15, blank=True)
    guardian_relation = models.CharField(max_length=50, blank=True)

    admission_date = models.DateField(auto_now_add=True)
    is_active      = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.enrollment_no})"


# ─────────────────────────────────────────────
#  ATTENDANCE
# ─────────────────────────────────────────────
class Attendance(models.Model):
    STATUS_CHOICES = [('P','Present'),('A','Absent'),('L','Leave')]

    student  = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    subject  = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date     = models.DateField()
    status   = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('student', 'subject', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} – {self.subject} – {self.date} – {self.status}"


# ─────────────────────────────────────────────
#  MARKS / RESULT
# ─────────────────────────────────────────────
class ExamType(models.Model):
    name       = models.CharField(max_length=50)   # Mid-Term, End-Term, Internal, Practical
    max_marks  = models.PositiveSmallIntegerField(default=100)
    pass_marks = models.PositiveSmallIntegerField(default=35)

    def __str__(self):
        return self.name


class Marks(models.Model):
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    subject   = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    obtained  = models.DecimalField(max_digits=5, decimal_places=2,
                                    validators=[MinValueValidator(0)])
    semester  = models.ForeignKey(Semester, on_delete=models.CASCADE)
    entered_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    entered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_type', 'semester')

    @property
    def is_pass(self):
        return self.obtained >= self.exam_type.pass_marks

    @property
    def percentage(self):
        return round((self.obtained / self.exam_type.max_marks) * 100, 2)

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.exam_type} = {self.obtained}"


# ─────────────────────────────────────────────
#  NOTICE BOARD
# ─────────────────────────────────────────────
class Notice(models.Model):
    AUDIENCE_CHOICES = [('all','All'),('student','Students'),('teacher','Teachers')]
    title      = models.CharField(max_length=255)
    content    = models.TextField()
    audience   = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='all')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active  = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
