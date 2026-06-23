from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
import json
from quiz.models import PDFDocument, Question
from .models import GameAttempt
from django.views.decorators.csrf import csrf_exempt

def play_game(request, pdf_id):
    pdf_doc = get_object_or_404(PDFDocument, id=pdf_id)
    ai_message = request.session.pop('ai_message', '')
    return render(request, 'game/play.html', {'pdf_id': pdf_id, 'pdf_title': pdf_doc.title, 'ai_message': ai_message})

def get_questions(request, pdf_id):
    pdf_doc = get_object_or_404(PDFDocument, id=pdf_id)
    questions = Question.objects.filter(pdf=pdf_doc)
    questions_data = []
    limit = request.GET.get('limit')
    
    for q in questions:
        questions_data.append({
            'id': q.id,
            'question': q.question_text,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'correct_answer': q.correct_answer,
            'explanation': q.explanation
        })
        
    if limit and limit.isdigit():
        questions_data = questions_data[:int(limit)]
    
    if not questions_data:
        print(f"DEBUG: No questions found in DB for PDF ID {pdf_id}")
        
    return JsonResponse({'questions': questions_data, 'count': len(questions_data)})

@csrf_exempt
def submit_score(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pdf_doc = get_object_or_404(PDFDocument, id=data.get('pdf_id'))
        
        attempt = GameAttempt.objects.create(
            pdf=pdf_doc,
            user=request.user if request.user.is_authenticated else None,
            total_questions=data.get('total_questions', 0),
            correct_answers=data.get('correct_answers', 0),
            wrong_answers=data.get('wrong_answers', 0),
            score=data.get('score', 0),
            accuracy=data.get('accuracy', 0.0),
            attempt_log=data.get('attempt_log', [])
        )
        return JsonResponse({'status': 'success', 'attempt_id': attempt.id})
    return JsonResponse({'status': 'error'})

def show_result(request, attempt_id):
    attempt = get_object_or_404(GameAttempt, id=attempt_id)
    return render(request, 'game/result.html', {'attempt': attempt})

@login_required(login_url='/quiz/login/')
def dashboard(request):
    # Fetch last 10 attempts to show progress trend
    last_attempts = GameAttempt.objects.filter(user=request.user).order_by('started_at')
    
    # We want to show the last 10 on the chart
    chart_attempts = last_attempts.reverse()[:10][::-1]
    
    test_labels = [f"Test {last_attempts.filter(started_at__lte=a.started_at).count()}" for a in chart_attempts]
    accuracies = [round(a.accuracy, 1) for a in chart_attempts]
    
    overall_avg = GameAttempt.objects.filter(user=request.user).aggregate(Avg('accuracy'))['accuracy__avg'] or 0
    total_days_active = GameAttempt.objects.filter(user=request.user).dates('started_at', 'day').count()
    
    advisories = []
    attempted_pdfs = PDFDocument.objects.filter(gameattempt__user=request.user).distinct()
    
    for idx, pdf in enumerate(attempted_pdfs):
        pdf_attempts = GameAttempt.objects.filter(user=request.user, pdf=pdf)
        pdf_avg = pdf_attempts.aggregate(Avg('accuracy'))['accuracy__avg'] or 0
        pdf_avg = round(pdf_avg, 1)
        
        if pdf_avg >= 80:
            advice = "Congratulations. Your corrected score is high and your base concept is strong."
            color = "#10b981" # Green
        elif pdf_avg >= 50:
            advice = "More practice is needed. Revise examples and repeat one short game round."
            color = "#fbbf24" # Yellow
        else:
            advice = "Needs improvement. Revise this chapter neatly from the PDF before replaying."
            color = "#ef4444" # Red
            
        advisories.append({
            'chapter_name': f"Chapter {idx + 1}: {pdf.title}",
            'accuracy': pdf_avg,
            'advice': advice,
            'color': color,
            'pdf_id': pdf.id
        })
        
    latest_2 = GameAttempt.objects.filter(user=request.user).order_by('-started_at')[:2]
    trend_str = "0%"
    if len(latest_2) == 2:
        diff = latest_2[0].accuracy - latest_2[1].accuracy
        trend_str = f"{'+' if diff > 0 else ''}{round(diff, 1)}%"
        
    context = {
        'dates_json': json.dumps(test_labels),
        'accuracies_json': json.dumps(accuracies),
        'overall_avg': round(overall_avg, 1),
        'total_days_active': total_days_active,
        'trend': trend_str,
        'advisories': advisories,
        'has_data': GameAttempt.objects.filter(user=request.user).exists()
    }
    
    return render(request, 'game/dashboard.html', context)
