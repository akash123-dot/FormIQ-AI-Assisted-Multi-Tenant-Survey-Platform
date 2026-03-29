from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage
from .models_mongo import Survey, Question
from .forms import ResultAIForm
from django.shortcuts import render, redirect
import json
from surveys.views import Question_View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from surveys.models import SurveyLink
from django_ratelimit.decorators import ratelimit
from smart_survey.settings import GOOGLE_API_KEY
from django.contrib import messages
from django.contrib.auth.decorators import login_required

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def SurveyView(survey_id: str) -> dict:
    """
    Fetch survey name and existing questions.
    Input: survey_id (string)
    Output: {"survey_name": str, "questions": [list of question texts]}
    """
    try:
        survey_obj = Survey.objects.get(id=survey_id)
        questions = Question.objects.filter(survey=survey_obj)  
        return {
            "survey_name": survey_obj.title,
            "questions": [q.text for q in questions]
        }
    except Survey.DoesNotExist:
        return {"error": f"Survey {survey_id} not found"}


tools = [SurveyView]


model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.4,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key = GOOGLE_API_KEY
 
).bind_tools(tools)



def model_call(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(content="""
You are an AI assistant that helps to generate survey questions.

When you receive a survey_id, you MUST call the `SurveyView` tool with that ID
to retrieve the survey_name and existing questions before based on that you are generating new questions that are not already in the survey also generate at lest 5 question if humanmessage = if this message sent and say somthing then generate based on that questions.

Return output as JSON list of new questions, like:
[
  {
    "text": "How satisfied are you with our platform?",
    "question_type": "single_choice",
    "options": ["Very", "Somewhat", "Not at all"]
  }
]
---> and remember one things 'question_type' should be one of 'single_choice', 'multiple_choice', 'text',
""")

    response = model.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    message = state['messages']
    last_message = message[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    else:
        return "end"
    
graph = StateGraph(AgentState)
graph.add_node('our_agent', model_call)
graph.add_node('tools', ToolNode(tools=tools))

graph.add_edge('tools', 'our_agent')

graph.set_entry_point('our_agent')

graph.add_conditional_edges(
    'our_agent',
    should_continue,
    {
        'continue': 'tools',
        'end': END
    }
)

app = graph.compile()

@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def ResultAIView(request, survey_id):
    get_object_or_404(SurveyLink, user=request.user.id, survey_id=survey_id)

    form = ResultAIForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user_input = form.cleaned_data['result']   

            try:
                inputs = {
                    "messages": [
                        HumanMessage(content=f"This is for survey ID {survey_id}. {user_input}")
                    ]
                }
                response = app.invoke(inputs)

               
                raw = response['messages'][-1].content

                
                if isinstance(raw, list):
                    raw = " ".join(
                        block.get("text", "") for block in raw
                        if isinstance(block, dict)
                    )

                raw = raw.strip()

                
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

               
                try:
                    questions = json.loads(raw)
                    if not isinstance(questions, list):
                        raise ValueError("Expected a JSON list")
                except (json.JSONDecodeError, ValueError):
                    messages.error(request, "AI returned an unexpected format. Please try again.")
                    return render(request, 'result_ai.html', {
                        'form': form,
                        'survey_id': survey_id
                    })

                if not questions:
                    messages.error(request, "AI could not generate questions. Try a different prompt.")
                    return render(request, 'result_ai.html', {
                        'form': form,
                        'survey_id': survey_id
                    })

                
                request.session['result'] = json.dumps(questions)
                json_data = json.dumps(questions)

                return render(request, 'result_ai.html', {
                    'form': form,
                    'data': questions,     
                    'json_data': json_data,
                    'survey_id': survey_id,
                })

            except Exception as e:
                error_msg = str(e).lower()

                if "quota" in error_msg or "limit" in error_msg or "429" in error_msg:
                    messages.error(request, "AI token limit reached. Please wait and try again.")
                elif "timeout" in error_msg:
                    messages.error(request, "AI request timed out. Please try again.")
                elif "api" in error_msg or "key" in error_msg:
                    messages.error(request, "AI service is unavailable. Please try later.")
                else:
                    messages.error(request, f"Something went wrong: {str(e)}")

                return render(request, 'result_ai.html', {
                    'form': form,
                    'survey_id': survey_id
                })

    return render(request, 'result_ai.html', {
        'form': form,
        'survey_id': survey_id
    })


def SaveAIQuestions(request, survey_id):

    if request.method == 'POST' and 'save_single' in request.POST:

     
        result_json = request.session.get('result')

        try:
            questions = json.loads(result_json)
        except:
            return HttpResponse("Invalid JSON in session", status=400)

        question_name = request.POST.get('text')

        for q in questions:
            if q.get('text') == question_name:

                Question.objects.create(
                    survey=survey_id,
                    text=q.get('text'),
                    question_type=q.get('question_type'),
                    options=q.get('options'),
                    is_ai_generated=True
                )

        return render(
            request,
            'result_ai.html',
            {
                'data': questions,          
                'survey_id': survey_id,
                'json_data': result_json    
            }
        )

    return HttpResponse("Invalid request", status=400)


def SaveAllAiQuestions(request, survey_id):
    if request.method == 'POST':
        raw_data = request.POST.get('data')

        try:
            data = json.loads(raw_data)  
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON data", status=400)

        for question_data in data:
            text = question_data.get('text')
            question_type = question_data.get('question_type')
            options = question_data.get('options')  

            Question.objects.create(
                survey=survey_id,
                text=text,
                question_type=question_type,
                options=options,
                is_ai_generated=True
            )

        return redirect(Question_View, survey_id=survey_id)
