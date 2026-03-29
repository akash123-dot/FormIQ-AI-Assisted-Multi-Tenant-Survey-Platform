from django.shortcuts import render, redirect
from surveys.models_mongo import Response, Survey, Question, Answer
from surveys.models import SurveyLink
from .forms import ResponseForm
from django.http import HttpResponseNotFound, HttpResponse
from bson.objectid import ObjectId


def TakeResponse(request, unique_id):
    if request.method == 'POST':
        survey = SurveyLink.objects.get(unique_id = unique_id)
        survey_id = survey.survey_id
        if survey_id is None:
            return HttpResponseNotFound("Survey not found")
        
        form = ResponseForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            response = Response(
                survey=survey_id,
                name=data['name'],
                email=data['email']
            )
            response.save()
            response_id = response.id
            return redirect('SubmitSurvey', survey_id=survey_id, response_id=response_id)
            
    else:
        form = ResponseForm()

    return render(request, 'response.html', {'form': form, 'unique_id': unique_id})
    

def SubmitSurvey(request, survey_id, response_id):
    if request.method == 'POST':
        response = Response.objects.get(id = response_id)
        if not response:
            return HttpResponseNotFound("Response not found")
        questions = Question.objects.filter(survey=ObjectId(survey_id))
        for question in questions:
            field_name = f"answer_{question.id}"
            answer_value = request.POST.getlist(field_name)
            if answer_value:
                for answer in answer_value:
                    Answer.objects.create(
                        response=response,
                        question=question,
                        answer_value=answer
                    ).save()

        return render(request, 'response_success.html')

    else:
        survey = Survey.objects.get(id = survey_id)
        questions = Question.objects.filter(survey=survey_id)
        return render(request, 'submit_survey.html', {'survey': survey,
                                                       'questions': questions,
                                                        'response_id': response_id})