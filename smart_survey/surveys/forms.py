from django import forms


class SurveyForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea)


class QuestionForm(forms.Form):
    text = forms.CharField(max_length=200)
    question_type = forms.ChoiceField(choices=[
        ('text', 'Text'),
        # ('int', 'Integer'),
        # ('bool', 'Boolean'),
        # ('float', 'Float'),
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
    ])
    options = forms.CharField(label="Options (comma separated for multiple choice, leave blank for text answer)", required=False)

class ResultAIForm(forms.Form):
    result = forms.CharField(widget=forms.Textarea)