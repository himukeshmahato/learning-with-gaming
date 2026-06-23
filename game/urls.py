from django.urls import path
from . import views

app_name = 'game'
urlpatterns = [
    path('play/<int:pdf_id>/', views.play_game, name='play'),
    path('api/questions/<int:pdf_id>/', views.get_questions, name='get_questions'),
    path('api/score/', views.submit_score, name='submit_score'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
