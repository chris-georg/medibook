from django import forms
from .models import Appointment
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# =========================
# REGISTER FORM (UI + FIXED)
# =========================
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)  # FIXED

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # KEEP: Tailwind UI styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                "class": "w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            })


# =========================
# APPOINTMENT FORM (MERGED VERSION)
# =========================
class AppointmentForm(forms.ModelForm):

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    # NEW: dynamic slots instead of raw time input
    time = forms.ChoiceField(choices=[])

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'reason']

        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),

            'doctor': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

    def __init__(self, *args, available_slots=None, **kwargs):
        super().__init__(*args, **kwargs)

        # KEEP UI default state
        self.fields['time'].widget.attrs.update({
            "class": "w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
        })

        # NEW LOGIC: dynamic slot injection
        if available_slots is not None:
            self.fields['time'].choices = [('', '-- Select a time slot --')] + [
                (slot, slot) for slot in available_slots
            ]
        else:
            self.fields['time'].choices = [('', '-- Select date and doctor first --')]