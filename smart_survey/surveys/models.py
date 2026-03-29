from django.db import models
from uuid import uuid4
from django.contrib.auth.models import User



class SurveyLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=255)
    survey_id = models.CharField(max_length=255)
    unique_id = models.UUIDField(default=uuid4, editable=False, primary_key=True, serialize=False)
    link = models.CharField(unique=True, null=True, blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)


