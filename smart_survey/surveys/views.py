from django.shortcuts import render, redirect
from .forms import SurveyForm, QuestionForm
from .models_mongo import Survey, Question, Response, Answer
from .models import SurveyLink
from bson.objectid import ObjectId
from django.contrib import messages
# import plotly.express as px
# import pandas as pd
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
import json 

@ratelimit(key="user_or_ip", rate="60/m", block=True)
def home(request):
    return render(request, 'home.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)


@login_required
@ratelimit(key="user", rate="30/m",method="POST", block=True)
def SurveyView(request):
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            survey = Survey(
                title=data['title'],
                description=data['description']
            )
            survey.save()
            # save survey in sql database with name and survey_id
            save_link, created = SurveyLink.objects.update_or_create(user=request.user, name=data['title'], survey_id=survey.id)
            if created:
                save_link.link = request.build_absolute_uri(f"/start-survey/{save_link.unique_id}")
                save_link.save()

            return redirect(Question_View, survey_id=survey.id)
    else:
        form = SurveyForm()
    return render(request, 'survey.html', {'form': form})


@login_required
@ratelimit(key="user", rate="30/m",method="POST", block=True)
def Question_View(request, survey_id):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            question_list = []
            question_type = data['question_type']
            options = data['options']
            if question_type in ['single_choice', 'multiple_choice', 'int', 'float'] and options:
                options = options.split(',')
                for option in options:
                    question_list.append(option.strip())

            question = Question(
                survey=ObjectId(survey_id),
                text=data['text'],
                question_type=question_type,
                options=question_list
            )
            question.save()
            return redirect(Question_View, survey_id=survey_id)
  
    else:
        form = QuestionForm()
        # get_object_or_404(SurveyLink, user = request.user.id, survey_id=survey_id)
    return render(request, 'question.html', {'form': form, 'survey_id': survey_id,})



@login_required
@ratelimit(key="user", rate="30/m", block=True)
def ShowAllSurveys(request):
    surveys = SurveyLink.objects.filter(user=request.user.id)
    return render(request, 'show_all_surveys.html', {'surveys': surveys})

@login_required
@ratelimit(key="user", rate="30/m", block=True)
def ShowSurveyView(request, survey_id):
    surveys = SurveyLink.objects.filter(user = request.user)
    for survey in surveys:
        if str(survey_id) == str(survey.survey_id):     #-----------------------------------------------------------------------------------------------------------------
            survey = Survey.objects.get(id=survey_id)
            questions = Question.objects.filter(survey=ObjectId(survey_id))
            return render(request, 'show_survey.html', {'survey': survey, 'questions': questions, 'survey_id': survey_id})
        
    
    raise Http404("Page not found")
        
@login_required
@ratelimit(key="user", rate="30/m", block=True)
def DeleteSurvey(request, survey_id):
    try:
        # Delete answers and responses related to this survey
        responses = Response.objects.filter(survey=ObjectId(survey_id))
        for response in responses:
            Answer.objects.filter(response=response.id).delete()
        responses.delete()

        # Delete all questions of this survey
        Question.objects.filter(survey=ObjectId(survey_id)).delete()

        # Delete the survey itself
        Survey.objects.filter(id=ObjectId(survey_id)).delete()

        # Delete the SurveyLink 
        SurveyLink.objects.filter(survey_id=survey_id).delete()

        messages.success(request, 'Survey deleted successfully.')

        return redirect(ShowAllSurveys)

    except Survey.DoesNotExist:
        messages.error(request, 'Survey not found.')
        return redirect(ShowAllSurveys)



@login_required
@ratelimit(key="user", rate="30/m", block=True)
def DownloadSurvey(request, survey_id):
    get_object_or_404(SurveyLink, user=request.user.id, survey_id=survey_id)

    try:
        survey_obj = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        raise Http404("Survey not found")

    questions = Question.objects.filter(survey=survey_obj)

    output = {
        "survey_id": str(survey_obj.id),
        "survey_title": survey_obj.title,
        "survey_description": survey_obj.description or "",
        "total_responses": Response.objects.filter(survey=survey_obj).count(),
        "questions": []
    }

    for question in questions:
        answers = Answer.objects.filter(question=question)
        answer_list = [ans.answer_value for ans in answers]

        output["questions"].append({
            "question_id": str(question.id),
            "question_text": question.text,
            "question_type": question.question_type,
            "options": question.options or [],
            "answers": answer_list,
            "total_answers": len(answer_list)
        })

    
    response = HttpResponse(
        json.dumps(output, indent=2, ensure_ascii=False),
        content_type="application/json"
    )
    response["Content-Disposition"] = f'attachment; filename="survey_{survey_id}.json"'
    return response
    



@login_required
@ratelimit(key="user", rate="30/m", block=True)
def BuildDiagram(request, survey_id):
    get_object_or_404(SurveyLink, user=request.user.id, survey_id=survey_id)

    try:
        survey_obj = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Survey not found"}, status=404)

    total_surveys = Response.objects.filter(survey=survey_obj).count()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
           
            questions = Question.objects.filter(
                survey=survey_obj,
                question_type__nin=['text']   
            )

            chart_data = []
            for question in questions:
                answers = Answer.objects.filter(question=question)
                
                counts = {}
                for ans in answers:
                    val = ans.answer_value
                    counts[val] = counts.get(val, 0) + 1

                if not counts:
                    continue  

                chart_data.append({
                    "question_id": str(question.id),
                    "question_text": question.text,
                    "question_type": question.question_type,
                    "labels": list(counts.keys()),
                    "values": list(counts.values()),
                })

            return JsonResponse({
                "status": "ok",
                "total_surveys": total_surveys,
                "charts": chart_data
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

   
    return render(request, "graphs/build_diagram.html", {
        "survey_id": survey_id,
        "total_surveys": total_surveys,
    })