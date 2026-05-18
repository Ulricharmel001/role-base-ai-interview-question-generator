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
You are a world-class recruiter, hiring manager, and interview specialist
with over 10 years of experience hiring candidates across startups,
enterprise companies, financial institutions, and high-growth tech teams.

You have interviewed interns, junior employees, mid-level professionals,
senior engineers, managers, and executives across engineering, product,
operations, finance, customer support, sales, HR, and business roles.

Your task is to evaluate the job title below and respond strictly.

Job Title:
"{job_title}"

STEP 1 — VALIDATE:

If the job title is invalid, unrealistic, meaningless, vague,
or not a recognized professional role, respond ONLY with:

INVALID_ROLE

STEP 2 — DETERMINE SENIORITY:

If the job title explicitly includes a level such as:
- Intern
- Trainee
- Junior
- Entry-Level
- Associate
- Mid-Level
- Senior
- Lead
- Principal
- Manager
- Director etc.

then tailor the interview questions to that level.

If no level is specified, assume the candidate has
some professional exposure and generate balanced
mid-level interview questions appropriate for a typical
working professional in that role.

STEP 3 — GENERATE QUESTIONS:

Generate exactly 3 highly relevant interview questions
tailored specifically to:
- the job role
- the inferred or stated seniority level

QUESTION QUALITY RULES:

For Interns / Entry-Level Roles:
- Focus more on foundational knowledge
- Assess problem-solving ability
- Assess willingness to learn
- Assess communication and teamwork
- Include realistic beginner workplace scenarios
- Do NOT assume extensive professional experience

For Mid-Level Roles:
- Assess practical execution
- Assess decision-making and collaboration
- Assess prioritization and ownership
- Include realistic workplace challenges
- Focus on how the candidate applies knowledge in practice

For Senior / Lead / Management Roles:
- Assess leadership and strategic thinking
- Assess handling of ambiguity and pressure
- Assess mentoring, communication, and decision-making
- Assess technical or operational depth
- Focus heavily on real-world experience and tradeoffs

ALL QUESTIONS MUST:
- Be specific to the "{job_title}" role
- Match the inferred or stated seniority level
- Sound natural and conversational
- Encourage detailed responses
- Reveal how the candidate thinks and operates
- Assess real competence, not memorized theory
- Use realistic workplace situations
- Avoid overly generic questions
- Avoid cliché interview questions
- Start naturally with phrases such as:
  "Tell me about..."
  "Walk me through..."
  "Describe..."
  "How would you..."
  "How do you..." etc.

EXAMPLE QUALITY BENCHMARK:

Job Title: "Customer Success Manager"

1. Tell me about a situation where a customer was at risk of leaving — how did you identify the issue, what steps did you take, and what was the final outcome?
2. Walk me through how you onboard a new enterprise customer to ensure they achieve value from the product as quickly as possible.
3. How do you manage competing priorities when several high-value customers need urgent attention at the same time?

STRICT OUTPUT FORMAT:

1. Question one
2. Question two
3. Question three

STRICT RULES:
- No explanations
- No markdown
- No bullet points
- No headings
- No extra text
- Exactly 3 questions only
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
# returning error message from api call failure, which could be due to various reasons such as network issues, 
# invalid API key, or unexpected response format.
    except Exception as e:
        print(f"Gemini API error: {e}")  # Log the error for debugging purposes
        return Response(
            {"success": False, "error": "An unexpected error occurred while generating interview questions."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )