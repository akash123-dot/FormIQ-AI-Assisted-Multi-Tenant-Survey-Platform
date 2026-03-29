"""
URL configuration for smart_survey project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from surveys import views
from surveys.views_ai import ResultAIView, SaveAllAiQuestions, SaveAIQuestions
from response import views as response_views
from django.contrib.auth import views as auth_views
from user import views as account_views



urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home, name='home'),
    path("survey/", views.SurveyView, name='create-survey'),
    path("question/<str:survey_id>", views.Question_View, name='question'),
    # path("save-survey-link/<survey_id>", views.SaveSurveyLink, name='save-survey-link'),
    path("show-survey/<str:survey_id>", views.ShowSurveyView, name='show-survey'),
    path("show-all-surveys", views.ShowAllSurveys, name='show-all-surveys'),
    path("AI-survey/<str:survey_id>", ResultAIView, name='AI-survey'),
    path("SaveAllAiQuestions/<str:survey_id>", SaveAllAiQuestions, name='SaveAllAiQuestions'),

    # for user who click on the survey link
    path("start-survey/<unique_id>", response_views.TakeResponse, name='TakeResponse'),
    path('submit-survey/<str:survey_id>/<str:response_id>/', response_views.SubmitSurvey, name='SubmitSurvey'),

    # delete my survey
    path("delete-survey/<str:survey_id>", views.DeleteSurvey, name='delete-survey'),
    

    # Build charts
    # path("show-chart/<str:survey_id>", views.BuildDiagram, name='show-chart'),
    path("surveys/<str:survey_id>/analytics/", views.BuildDiagram, name="build_diagram"),

    #download survey
    path("surveys/<str:survey_id>/download/", views.DownloadSurvey, name="download-survey"),

    #save single question
    path("save-question/<str:survey_id>", SaveAIQuestions, name='save-question'),

    #login and register
    path('register/', account_views.registration, name='registration'),
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='account/logout.html'), name='logout'),


]
