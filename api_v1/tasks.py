import os
import json
import logging
from celery import shared_task
import google.generativeai as genai

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

    prompt = f"""
    Jesteś precyzyjnym i surowym nauczycielem oceniającym odpowiedź na pytanie w quizie. Twoim zadaniem jest ocenić odpowiedź użytkownika, bazując na podanych kryteriach oceniania.

    Oto szczegóły:
    1. Pytanie: "{question_text}"
    2. Kryteria Oceniania: "{grading_criteria}"
    3. Maksymalna liczba punktów do zdobycia za to pytanie: {max_points}
    4. Odpowiedź Użytkownika: "{user_answer}"

    Twoje zadania:
    - Oceń, w jakim stopniu odpowiedź użytkownika spełnia kryteria oceniania.
    - Przyznaj liczbę punktów od 0 do {max_points}. Bądź sprawiedliwy, ale wymagający. Nie przyznawaj punktów, jeśli odpowiedź nie odnosi się do kryteriów. Nie odejmuj punktów za błędy ortograficzne, gramatyczne czy stylistyczne, chyba że są one kluczowe dla zrozumienia odpowiedzi.
    - Napisz krótkie, jedno- lub dwuzdaniowe uzasadnienie swojej oceny w języku polskim, wyjaśniając, dlaczego przyznałeś tyle punktów (np. co było dobrze, a czego zabrakło).

    Zwróć swoją ocenę jako idealnie sformatowany obiekt JSON. Bez żadnych dodatkowych znaków, komentarzy czy formatowania markdown. JSON musi zawierać DOKŁADNIE dwa klucze: "score" (typu integer) i "feedback" (typu string).
    """

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
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