from celery import shared_task
import time

@shared_task
def generate_ai_answer(question_id):
    """
    A dummy task that simulates generating an AI answer.
    In a real application, this would involve calling an AI model.
    """
    print(f"Generating AI answer for question {question_id}...")
    # Simulate a long-running task
    time.sleep(10)
    result = f"This is the AI-generated answer for question {question_id}."
    print(f"Finished generating AI answer for question {question_id}.")
    return result