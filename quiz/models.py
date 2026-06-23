from django.db import models
from django.contrib.auth.models import User

class PDFDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploaded_pdfs/')
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TextChunk(models.Model):
    pdf = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_number = models.IntegerField()
    chunk_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pdf.title} - Chunk {self.chunk_number}"

class Question(models.Model):
    pdf = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name="questions")
    chunk = models.ForeignKey(TextChunk, on_delete=models.SET_NULL, null=True, blank=True)
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[('A','A'), ('B','B'), ('C','C'), ('D','D')])
    explanation = models.TextField(blank=True, null=True)
    topic = models.CharField(max_length=100, blank=True, null=True)
    difficulty = models.CharField(max_length=50, default="Medium")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text
