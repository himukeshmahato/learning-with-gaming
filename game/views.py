from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from quiz.models import PDFDocument, Question

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
        
    return JsonResponse({'questions': questions_data, 'count': len(questions_data)})
