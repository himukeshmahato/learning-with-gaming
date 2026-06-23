from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import PDFDocumentForm, UserRegisterForm
from .models import PDFDocument, TextChunk, Question
from .utils import extract_text_from_pdf, chunk_text
from .ai_generator import generate_questions_from_chunk, get_available_models
import os
import threading
from django.db import connection

def _bg_generate_questions(pdf_id, chunks, preferred_model="auto"):
    """Background task to generate questions for the remaining chunks."""
    try:
        # Re-fetch the PDF in this thread
        from .models import PDFDocument, TextChunk, Question
        pdf_doc = PDFDocument.objects.get(id=pdf_id)
        
        for index, c_text in enumerate(chunks):
            chunk = TextChunk.objects.create(
                pdf=pdf_doc,
                chunk_number=index + 2, # +2 because index starts at 0 and chunk 1 is sync
                chunk_text=c_text
            )
            
            # Request 15 questions per chunk
            result = generate_questions_from_chunk(c_text, number_of_questions=15, preferred_model=preferred_model)
            ai_questions = result["questions"]
            for q_data in ai_questions:
                correct_ans = q_data.get("correct_answer") or q_data.get("answer")
                if not correct_ans or not q_data.get("question"):
                    continue
                
                Question.objects.create(
                    pdf=pdf_doc,
                    chunk=chunk,
                    question_text=q_data.get("question"),
                    option_a=q_data.get("options", {}).get("A", ""),
                    option_b=q_data.get("options", {}).get("B", ""),
                    option_c=q_data.get("options", {}).get("C", ""),
                    option_d=q_data.get("options", {}).get("D", ""),
                    correct_answer=correct_ans,
                    explanation=q_data.get("explanation", ""),
                    topic=q_data.get("topic", "General"),
                    difficulty=q_data.get("difficulty", "Medium")
                )
    finally:
        connection.close() # Ensure DB connection is closed in thread

def upload_pdf(request):
    if request.method == 'POST':
        form = PDFDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_doc = form.save(commit=False)
            if request.user.is_authenticated:
                pdf_doc.user = request.user
            pdf_doc.save()

            # Get selected model from form
            preferred_model = request.POST.get('llm_model', 'auto')

            # Process PDF
            text = extract_text_from_pdf(pdf_doc.file.path)
            pdf_doc.extracted_text = text
            pdf_doc.save()

            # Chunk text and generate questions
            chunks = chunk_text(text, max_chars=4000)
            
            # 1. GENERATE FIRST 5 QUESTIONS SYNCHRONOUSLY (Quick Start)
            first_chunk_text = chunks[0] if chunks else ""
            ai_message = ""
            if first_chunk_text:
                chunk = TextChunk.objects.create(
                    pdf=pdf_doc,
                    chunk_number=1,
                    chunk_text=first_chunk_text
                )
                # Quick 5 questions for first chunk
                result = generate_questions_from_chunk(first_chunk_text, number_of_questions=5, preferred_model=preferred_model)
                ai_questions = result["questions"]
                ai_message = result.get("message", "")
                
                # If the preferred model failed, use whatever model worked for bg too
                if result.get("fallback") and result.get("model_used"):
                    preferred_model = result["model_used"]
                
                for q_data in ai_questions:
                    correct_ans = q_data.get("correct_answer") or q_data.get("answer")
                    if not correct_ans or not q_data.get("question"):
                        continue
                    
                    Question.objects.create(
                        pdf=pdf_doc,
                        chunk=chunk,
                        question_text=q_data.get("question"),
                        option_a=q_data.get("options", {}).get("A", ""),
                        option_b=q_data.get("options", {}).get("B", ""),
                        option_c=q_data.get("options", {}).get("C", ""),
                        option_d=q_data.get("options", {}).get("D", ""),
                        correct_answer=correct_ans,
                        explanation=q_data.get("explanation", ""),
                        topic=q_data.get("topic", "General"),
                        difficulty=q_data.get("difficulty", "Medium")
                    )

            # 2. START BACKGROUND THREAD FOR REMAINING CHUNKS (up to 4 more)
            remaining_chunks = chunks[1:5]
            if remaining_chunks:
                bg_thread = threading.Thread(target=_bg_generate_questions, args=(pdf_doc.id, remaining_chunks, preferred_model))
                bg_thread.daemon = True
                bg_thread.start()

            # Store AI message in session to show on the game page
            if ai_message:
                request.session['ai_message'] = ai_message

            # Redirect immediately if at least some questions are likely being created
            return redirect('game:play', pdf_id=pdf_doc.id)
    else:
        form = PDFDocumentForm()
    
    available_models = get_available_models()
    return render(request, 'quiz/upload.html', {'form': form, 'available_models': available_models})


def register_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('quiz:upload')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('quiz:upload')
    else:
        form = AuthenticationForm()
    # Apply styling classes regardless of method
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-input'})
    return render(request, 'registration/login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('quiz:upload')
