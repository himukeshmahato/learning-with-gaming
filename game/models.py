from django.db import models
from django.contrib.auth.models import User
from quiz.models import PDFDocument

class GameAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    pdf = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    level_reached = models.IntegerField(default=1)
    attempt_log = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Attempt by {self.user} on {self.pdf.title}"
