from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .forms import RegisterForm, AppointmentForm
from .models import Appointment, Doctor
from datetime import datetime, date, timedelta
import datetime as dt

def health(request):
    return HttpResponse("OK", status=200)
    
# --- Helper: Generate all 15-min slots within working hours ---
def generate_time_slots():
    slots = []
    # Morning: 8:00 AM - 1:00 PM
    morning_start = dt.time(8, 0)
    morning_end = dt.time(13, 0)
    # Afternoon: 3:00 PM - 6:00 PM
    afternoon_start = dt.time(15, 0)
    afternoon_end = dt.time(18, 0)

    for session_start, session_end in [
        (morning_start, morning_end),
        (afternoon_start, afternoon_end)
    ]:
        current = datetime.combine(date.today(), session_start)
        end = datetime.combine(date.today(), session_end)
        while current < end:
            slots.append(current.strftime('%H:%M'))
            current += timedelta(minutes=15)
    return slots


# --- Helper: Get available slots for a doctor on a date ---
def get_available_slots(doctor, selected_date):
    all_slots = generate_time_slots()
    MAX_APPOINTMENTS = 36  # 15-min slots across both sessions

    # Get all active bookings for this doctor on this date
    booked = Appointment.objects.filter(
        doctor=doctor,
        date=selected_date,
    ).exclude(status='Cancelled').values_list('time', flat=True)

    # Format booked times to HH:MM for comparison
    booked_times = [t.strftime('%H:%M') for t in booked]

    # Check daily capacity
    if len(booked_times) >= MAX_APPOINTMENTS:
        return []  # Fully booked

    available = [slot for slot in all_slots if slot not in booked_times]
    return available


# Home page
def home(request):
    return render(request, 'home.html')


# Register
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')  # 👈 admin goes here
            return redirect('dashboard')            # 👈 patient goes here
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


# Logout
def logout_view(request):
    logout(request)
    return redirect('home')


# Patient dashboard
@login_required
def dashboard(request):
    appointments = Appointment.objects.filter(
    patient=request.user
).order_by('-created_at')
    return render(request, 'dashboard.html', {'appointments': appointments})


# AJAX — fetch available slots when doctor + date is selected
@login_required
def get_slots(request):
    doctor_id = request.GET.get('doctor_id')
    selected_date = request.GET.get('date')

    if not doctor_id or not selected_date:
        return JsonResponse({'slots': [], 'message': 'Missing info'})

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
        parsed_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

        # Block past dates
        if parsed_date < date.today():
            return JsonResponse({'slots': [], 'message': 'Cannot book past dates.'})

        # Block Sundays
        if parsed_date.weekday() == 6:
            return JsonResponse({'slots': [], 'message': 'No appointments on Sundays.'})

        slots = get_available_slots(doctor, parsed_date)

        # If today, remove slots where the time has already passed
        if parsed_date == date.today():
            now = dt.datetime.now().time()
            slots = [slot for slot in slots if dt.datetime.strptime(slot, '%H:%M').time() > now]

        if not slots:
            return JsonResponse({'slots': [], 'message': 'No available slots for this date.'})

        return JsonResponse({'slots': slots, 'message': ''})

    except Doctor.DoesNotExist:
        return JsonResponse({'slots': [], 'message': 'Doctor not found.'})

# Book appointment
@login_required
def book_appointment(request):
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')
        reason = request.POST.get('reason')

        try:
            doctor = Doctor.objects.get(pk=doctor_id)
            parsed_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            parsed_time = datetime.strptime(selected_time, '%H:%M').time()

            # Validate slot is still available
            available_slots = get_available_slots(doctor, parsed_date)

            if not available_slots:
                messages.error(request, f'Dr. {doctor.name} is fully booked on this date.')
            elif selected_time not in available_slots:
                messages.error(request, f'That time slot is no longer available. Please choose another.')
            elif parsed_date < date.today():
                messages.error(request, 'You cannot book a past date.')
            elif parsed_date.weekday() == 6:
                messages.error(request, 'No appointments are available on Sundays.')
            elif parsed_date == date.today() and parsed_time <= dt.datetime.now().time():
                messages.error(request, 'That time slot has already passed. Please choose a future time.')
            else:
                Appointment.objects.create(
                    patient=request.user,
                    doctor=doctor,
                    date=parsed_date,
                    time=parsed_time,
                    reason=reason,
                    duration=15,
                )
                messages.success(request, f'Appointment booked with Dr. {doctor.name} on {parsed_date} at {selected_time}!')
                return redirect('dashboard')

        except Exception as e:
            messages.error(request, 'Something went wrong. Please try again.')

    return render(request, 'book_appointment.html', {'doctors': doctors})

# Cancel appointment
@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    appointment.status = 'Cancelled'
    appointment.save()
    messages.success(request, 'Appointment cancelled.')
    return redirect('dashboard')


# Admin dashboard
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    appointments = Appointment.objects.all().order_by('-created_at')
    return render(request, 'admin_dashboard.html', {'appointments': appointments})


# Admin update status
@login_required
def update_status(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = request.POST['status']
        appointment.save()
        messages.success(request, 'Status updated.')
    return redirect('admin_dashboard')
