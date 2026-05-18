from django.urls import path
from .views import generate_questions

urlpatterns = [
    path("questions/", generate_questions),
]
