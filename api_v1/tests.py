import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status

# Utworzenie tymczasowego katalogu media na potrzeby testów
# Będzie on używany przez dekorator @override_settings
TEST_MEDIA_DIR = Path(tempfile.gettempdir()) / 'django_test_media'


@override_settings(
    MEDIA_ROOT=TEST_MEDIA_DIR,
    SECRET_KEY='a-test-secret-key-for-development' # Dodany klucz, aby uniknąć błędów
)
class ApiViewsTestCase(APITestCase):
    """
    Zestaw testów dla widoków API: TestListView i QuestionListView.
    """

    @classmethod
    def setUpClass(cls):
        """
        Uruchamiane raz przed wszystkimi testami w tej klasie.
        Tworzy tymczasowy katalog na pliki testowe.
        """
        super().setUpClass()
        os.makedirs(TEST_MEDIA_DIR / 'tests', exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """
        Uruchamiane raz po wszystkich testach w tej klasie.
        Usuwa tymczasowy katalog.
        """
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_DIR, ignore_errors=True)

    def setUp(self):
        """
        Uruchamiane przed każdym pojedynczym testem.
        Tworzy fałszywe pliki JSON z danymi testowymi, zgodne z serializerem.
        """
        self.tests_dir = TEST_MEDIA_DIR / 'tests'
        
        # Dane dla testu 1 (historia) - z pytaniami zamkniętymi i otwartym
        self.historia_data = {
            "category": "Historia", "scope": "Polska", "version": "1.0",
            "questions": [
                {"id": 1, "questionText": "Kto był pierwszym królem Polski?", "type": "single-choice", "tags": ["władcy", "Polska"], "options": ["Mieszko I", "Bolesław Chrobry", "Kazimierz Wielki"], "correctAnswers": [1], "explanation": "Wyjaśnienie do pytania 1."},
                {"id": 2, "questionText": "W którym roku odbył się chrzest Polski?", "type": "single-choice", "tags": ["daty", "Polska"], "options": ["966", "1025", "1410"], "correctAnswers": [0], "explanation": "Wyjaśnienie do pytania 2."},
                {"id": 3, "questionText": "Opisz przyczyny Unii Lubelskiej.", "type": "open-ended", "tags": ["unia", "polityka"], "gradingCriteria": "Musi wspomnieć o zagrożeniu moskiewskim i bezpotomnej śmierci Zygmunta Augusta.", "maxPoints": 5, "explanation": "Kluczowe były zagrożenie ze strony Moskwy oraz dążenie do zapewnienia trwałości związku Polski i Litwy."}
            ]
        }
        with open(self.tests_dir / 'historia.json', 'w', encoding='utf-8') as f:
            json.dump(self.historia_data, f)
            
        # Dane dla testu 2 (biologia) - tylko pytania zamknięte
        self.biologia_data = {
            "category": "Biologia", "scope": "Komórka", "version": "1.1",
            "questions": [
                {"id": 10, "questionText": "Co jest centrum energetycznym komórki?", "type": "single-choice", "tags": ["komórka", "organella"], "options": ["Jądro", "Rybosom", "Mitochondrium"], "correctAnswers": [2], "explanation": "Wyjaśnienie do pytania 10."},
                {"id": 11, "questionText": "Które z poniższych to organella?", "type": "multiple-choice", "tags": ["komórka", "organella"], "options": ["DNA", "RNA", "Aparat Golgiego", "Mitochondrium"], "correctAnswers": [2, 3], "explanation": "Wyjaśnienie do pytania 11."}
            ]
        }
        with open(self.tests_dir / 'biologia.json', 'w', encoding='utf-8') as f:
            json.dump(self.biologia_data, f)

    def tearDown(self):
        """
        Uruchamiane po każdym pojedynczym teście.
        Czyści katalog z testowymi plikami JSON.
        """
        for f in self.tests_dir.glob('*.json'):
            os.remove(f)

    # --- Testy dla TestListView ---

    def test_list_available_tests_success(self):
        """
        Sprawdza, czy endpoint /tests/ poprawnie zwraca listę metadanych testów
        wraz ze szczegółowym licznikiem pytań.
        """
        response = self.client.get('/api/v1/tests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        
        response_data.sort(key=lambda x: x['test_id'])

        self.assertEqual(response_data[0]['test_id'], 'biologia')
        self.assertEqual(response_data[0]['question_counts']['total'], 2)
        self.assertEqual(response_data[0]['question_counts']['closed'], 2)
        self.assertEqual(response_data[0]['question_counts']['open'], 0)

        self.assertEqual(response_data[1]['test_id'], 'historia')
        self.assertEqual(response_data[1]['question_counts']['total'], 3)
        self.assertEqual(response_data[1]['question_counts']['closed'], 2)
        self.assertEqual(response_data[1]['question_counts']['open'], 1)
    
    def test_list_available_tests_empty(self):
        """
        Sprawdza, czy endpoint /tests/ zwraca pustą listę, gdy nie ma plików.
        """
        self.tearDown() 
        response = self.client.get('/api/v1/tests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    # --- Testy dla QuestionListView ---

    def test_get_questions_missing_params(self):
        """
        Sprawdza, czy brakujące parametry zwracają błąd 400.
        """
        response = self.client.get('/api/v1/questions/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'MISSING_PARAMETERS')

    def test_get_questions_more_than_available(self):
        """
        Sprawdza, czy żądanie większej liczby pytań niż dostępna zwraca wszystkie dostępne.
        """
        response = self.client.get('/api/v1/questions/', {'categories': 'biologia', 'num_questions': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        
    def test_question_shuffling_logic(self):
        """
        Kluczowy test: Sprawdza, czy po przelosowaniu opcji,
        indeksy 'correctAnswers' nadal wskazują na poprawne odpowiedzi tekstowe.
        """
        original_question = self.biologia_data['questions'][1]
        original_options = original_question['options']
        original_correct_indices = original_question['correctAnswers']
        original_correct_answers_text = {original_options[i] for i in original_correct_indices}

        response = self.client.get('/api/v1/questions/', {'categories': 'biologia', 'num_questions': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        shuffled_question = next((q for q in response_data if q['id'] == original_question['id']), None)
        self.assertIsNotNone(shuffled_question)

        if shuffled_question:
            shuffled_options = shuffled_question['options']
            shuffled_correct_indices = shuffled_question['correctAnswers']
            shuffled_correct_answers_text = {shuffled_options[i] for i in shuffled_correct_indices}
            self.assertEqual(original_correct_answers_text, shuffled_correct_answers_text)

    # --- NOWE TESTY: Filtrowanie pytań według trybu ---

    def test_get_questions_mode_closed_only(self):
        """Sprawdza, czy `mode=closed` zwraca tylko pytania zamknięte."""
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 2, 'mode': 'closed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.json()
        self.assertEqual(len(questions), 2)
        for q in questions:
            self.assertIn(q['type'], ['single-choice', 'multiple-choice'])
            self.assertIn('options', q) # Sprawdza poprawność serializera

    def test_get_questions_mode_open_only(self):
        """Sprawdza, czy `mode=open` zwraca tylko pytania otwarte."""
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 1, 'mode': 'open'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.json()
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['type'], 'open-ended')
        self.assertIn('gradingCriteria', questions[0]) # Sprawdza poprawność serializera
        self.assertNotIn('options', questions[0]) # Sprawdza poprawność serializera

    def test_get_questions_mode_mixed_default(self):
        """Sprawdza, czy domyślny tryb (mieszany) zwraca oba typy pytań."""
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.json()
        self.assertEqual(len(questions), 3)
        types = {q['type'] for q in questions}
        self.assertIn('open-ended', types)
        self.assertIn('single-choice', types)

    def test_get_questions_invalid_mode(self):
        """Sprawdza, czy błędna wartość `mode` zwraca błąd 400."""
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 1, 'mode': 'wrong_mode'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INVALID_MODE_PARAMETER')
    
    def test_get_questions_no_questions_for_mode(self):
        """Sprawdza, czy API zwraca 404, gdy brak pytań dla danego trybu."""
        # Biologia nie ma pytań otwartych
        response = self.client.get('/api/v1/questions/', {'categories': 'biologia', 'num_questions': 1, 'mode': 'open'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'NO_QUESTIONS_FOUND')



@override_settings(SECRET_KEY='a-test-secret-key-for-development')
class CheckOpenAnswerViewTestCase(APITestCase):
    """
    Zestaw testów dla widoku CheckOpenAnswerView.
    Testy te używają mockowania, aby uniknąć rzeczywistych zapytań do API Gemini.
    WAŻNE: Te testy zadziałają poprawnie tylko wtedy, gdy w pliku api_v1/views.py
    zostanie dodany import: `import google.generativeai as genai`
    """

    def setUp(self):
        """Przygotowanie danych do testów."""
        self.url = '/api/v1/check_answer/'
        self.payload = {
            'userAnswer': 'Unia była spowodowana zagrożeniem ze strony Moskwy i brakiem potomka u króla.',
            'gradingCriteria': 'Musi wspomnieć o zagrożeniu moskiewskim i bezpotomnej śmierci Zygmunta Augusta.',
            'questionText': 'Opisz przyczyny Unii Lubelskiej.',
            'maxPoints': 5
        }

    @patch('api_v1.views.genai.GenerativeModel')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'})
    def test_check_answer_success(self, mock_generative_model):
        """Sprawdza poprawne działanie endpointu przy udanej odpowiedzi od AI."""
        # Konfiguracja mocka
        mock_ai_response = MagicMock()
        mock_ai_response.text = json.dumps({"score": 4, "feedback": "Dobra odpowiedź."})
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_ai_response
        mock_generative_model.return_value = mock_model_instance

        # Wykonanie zapytania
        response = self.client.post(self.url, self.payload, format='json')

        # Asercje
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 4)
        self.assertEqual(response.data['feedback'], "Dobra odpowiedź.")
        mock_model_instance.generate_content.assert_called_once()

    @patch.dict(os.environ, clear=True) # Symulacja braku klucza API
    def test_check_answer_no_api_key(self):
        """Sprawdza, czy serwer zwraca błąd 500, gdy brakuje klucza API."""
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.data['error'], 'API_KEY_MISSING')
        self.assertIn('Klucz API do usługi AI nie jest skonfigurowany', response.data['message'])

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}) # FIX: Dodano mock klucza API
    def test_check_answer_missing_payload(self):
        """Sprawdza, czy serwer zwraca błąd 400 przy niekompletnych danych."""
        incomplete_payload = self.payload.copy()
        del incomplete_payload['userAnswer']
        response = self.client.post(self.url, incomplete_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INCOMPLETE_DATA')

    @patch('api_v1.views.genai.GenerativeModel')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'})
    def test_check_answer_ai_invalid_json(self, mock_generative_model):
        """Sprawdza obsługę błędu, gdy AI zwróci niepoprawny JSON."""
        mock_ai_response = MagicMock()
        mock_ai_response.text = "Przepraszam, wystąpił błąd." # Nie-JSON
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_ai_response
        mock_generative_model.return_value = mock_model_instance
        
        response = self.client.post(self.url, self.payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'AI_RESPONSE_INVALID_FORMAT')
        self.assertIn('Otrzymano nieprawidłowy format odpowiedzi', response.data['message'])

    @unittest.skipUnless(os.environ.get('GEMINI_API_KEY'), "GEMINI_API_KEY is not set, skipping integration test.")
    def test_integration_check_answer_real_api_call(self):
        """
        Test integracyjny wykonujący prawdziwe zapytanie do API Gemini.
        Ten test zostanie uruchomiony tylko, jeśli zmienna środowiskowa
        GEMINI_API_KEY jest ustawiona.
        """
        payload = {
            'userAnswer': 'Słońce jest gwiazdą.',
            'gradingCriteria': 'Odpowiedź musi stwierdzać, że Słońce jest gwiazdą.',
            'questionText': 'Czym jest Słońce?',
            'maxPoints': 1
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        # Sprawdzamy, czy zapytanie się powiodło
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sprawdzamy, czy odpowiedź ma poprawną strukturę
        response_data = response.json()
        self.assertIn('score', response_data)
        self.assertIn('feedback', response_data)
        self.assertIsInstance(response_data['score'], int)
        self.assertIsInstance(response_data['feedback'], str)

        print(f"\n--- Integration Test Response ---\n"
              f"Score: {response_data['score']}\n"
              f"Feedback: {response_data['feedback']}\n"
              f"-------------------------------")