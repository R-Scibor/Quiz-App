import os
import json
import logging
from celery import shared_task
import google.generativeai as genai
from .models import PromptConfiguration

logger = logging.getLogger(__name__)

@shared_task
def generate_ai_answer(user_answer, grading_criteria, question_text, max_points):
    """
    An asynchronous task to grade a user's answer using the Gemini AI.
    """
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        logger.critical("Klucz API Gemini (GEMINI_API_KEY) nie jest skonfigurowany na serwerze.")
        # In a real app, you might want to handle this more gracefully
        return {"error": "API_KEY_MISSING", "message": "Klucz API do usługi AI nie jest skonfigurowany na serwerze."}

    try:
        # Pobierz aktywny szablon promptu z bazy danych
        prompt_config = PromptConfiguration.objects.filter(is_active=True).first()
        if not prompt_config:
            logger.error("Brak aktywnego promptu w konfiguracji bazy danych.")
            return {"error": "NO_ACTIVE_PROMPT", "message": "Brak aktywnego promptu w konfiguracji."}

        # Użyj szablonu z bazy danych i wstaw dynamiczne wartości
        prompt = prompt_config.prompt_text.format(
            question_text=question_text,
            grading_criteria=grading_criteria,
            max_points=max_points,
            user_answer=user_answer
        )

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        ai_response = model.generate_content(prompt)

        cleaned_text = ai_response.text.strip().replace('```json', '').replace('```', '').strip()
        response_json = json.loads(cleaned_text)

        if 'score' not in response_json or 'feedback' not in response_json:
             raise ValueError("Odpowiedź AI nie zawiera wymaganych kluczy 'score' i 'feedback'.")

        return response_json
    except Exception as e:
        logger.exception("Wystąpił nieoczekiwany błąd podczas komunikacji z AI: %s", e)
        # Inform Celery that the task failed
        raise