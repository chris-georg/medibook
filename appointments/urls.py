from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update-status/<int:pk>/', views.update_status, name='update_status'),
    path('get-slots/', views.get_slots, name='get_slots'),
    path('health/', views.health, name='health'),
]
