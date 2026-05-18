import os
import google.generativeai as genai

from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# We will attempt to use the models in order of preference, falling back to the next one if we encounter a rate limit error. 
# This allows us to provide the best possible experience while navigating potential API limitations.
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash",
]

@api_view(["POST"])
def generate_questions(request):

    job_title = request.data.get("job_title", "").strip()
   # Basic validation to catch empty or obviously invalid input before hitting the API
    if not job_title:
        return Response(
            {"success": False, "error": "Job title is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(job_title) < 3 or not any(char.isalpha() for char in job_title):
        return Response(
            {"success": False, "error": "Please enter a valid professional job title."},
            status=status.HTTP_400_BAD_REQUEST
        )
# The prompt is designed to elicit a structured response while enforcing strict rules to ensure the output is clean and usable by the frontend.
    prompt = f"""
    You are an experienced HR professional and hiring manager.

    Your task is to evaluate and respond strictly.

    Job Title:
    "{job_title}"

    RULES:

    1. If the job title is invalid, unrealistic, meaningless,
       or not a real professional role, respond ONLY:

       INVALID_ROLE

    2. If valid, respond ONLY in this exact format:

       1. Question one
       2. Question two
       3. Question three

    STRICT RULES:
    - No explanations
    - No markdown
    - No bullet points
    - No extra text
    - Exactly 3 questions only
    - Thoughtful interview questions
    - Questions should assess practical experience
    - Questions should encourage detailed responses
    - Avoid generic questions
    - Focus on realistic workplace scenarios
    """

    try:
        ai_response = None
# Try each model in order, moving to the next if we hit a rate limit error
        for model_name in MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                ai_response = response.text.strip()
                break
            except Exception as e:
                if "429" in str(e):
                    continue
                raise

        if ai_response is None:
            return Response(
                {"success": False, "error": "All models are currently rate limited. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if "INVALID_ROLE" in ai_response:
            return Response(
                {"success": False, "error": "This does not appear to be a valid job title."},
                status=status.HTTP_400_BAD_REQUEST
            )
# Clean the response to ensure it strictly follows the expected format, removing any lines that don't start with a number followed by a period.
        lines = [line.strip() for line in ai_response.split("\n") if line.strip() and line.strip()[0].isdigit()]
        clean_response = "\n".join(lines[:3])

        return Response(
            {
                "success": True,
                "job_title": job_title,
                "questions": clean_response
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"Gemini API error: {e}")
        return Response(
            {"success": False, "error": "An unexpected error occurred while generating interview questions."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )