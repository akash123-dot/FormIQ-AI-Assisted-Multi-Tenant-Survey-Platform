from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField, DictField, BooleanField
from datetime import datetime


# -------------------- SURVEY --------------------
class Survey(Document):
    title = StringField(required=True, max_length=200)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'surveys'}

# -------------------- QUESTION --------------------
class Question(Document):
    survey = ReferenceField(Survey, required=True) 
    text = StringField(required=True)
    question_type = StringField(required=True, choices=[
        'text', 'int', 'float', 'bool', 'single_choice', 'multiple_choice'
    ])
    options = ListField(StringField())  
    is_ai_generated = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'questions'}

# -------------------- RESPONSE --------------------
class Response(Document):
    survey = ReferenceField(Survey, required=True)
    name = StringField(required=True)
    email = StringField(required=True)
    submitted_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'responses'}

# -------------------- ANSWER --------------------
class Answer(Document):
    response = ReferenceField(Response, required=True)
    question = ReferenceField(Question, required=True)
    answer_value = StringField(required=True)  

    meta = {'collection': 'answers'}