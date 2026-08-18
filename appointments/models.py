from django.db import models
from django.contrib.auth.models import User

class Doctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ('General', 'General Practitioner'),
        ('Cardiology', 'Cardiology'),
        ('Dentist', 'Dentist'),
        ('Pediatrics', 'Pediatrics'),
        ('Dermatology', 'Dermatology'),
    ]
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(default=15)  # duration in minutes
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} → Dr. {self.doctor.name} on {self.date} at {self.time}"