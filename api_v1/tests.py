import os
import json
import shutil
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

# --- Założenia ---
# Poniższy kod zakłada, że masz aplikację 'api_v1'
# a w niej pliki serializers.py z odpowiednimi serializerami.
# Ten plik (tests.py) powinien znajdować się w katalogu api_v1/.

# Utworzenie tymczasowego katalogu media na potrzeby testów
# Będzie on używany przez dekorator @override_settings
TEST_MEDIA_DIR = Path(tempfile.gettempdir()) / 'django_test_media'

@override_settings(MEDIA_ROOT=TEST_MEDIA_DIR)
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
        
        # Dane dla testu 1 (historia) - teraz z pytaniem open-ended
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
            
        # Dane dla testu 2 (biologia)
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
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        
        # Sortujemy listę, żeby mieć pewność co do kolejności
        response_data.sort(key=lambda x: x['test_id'])

        # Sprawdzamy dane dla biologii
        self.assertEqual(response_data[0]['test_id'], 'biologia')
        self.assertEqual(response_data[0]['question_counts']['total'], 2)
        self.assertEqual(response_data[0]['question_counts']['closed'], 2)
        self.assertEqual(response_data[0]['question_counts']['open'], 0)

        # Sprawdzamy dane dla historii
        self.assertEqual(response_data[1]['test_id'], 'historia')
        self.assertEqual(response_data[1]['question_counts']['total'], 3)
        self.assertEqual(response_data[1]['question_counts']['closed'], 2)
        self.assertEqual(response_data[1]['question_counts']['open'], 1)
    
    def test_list_available_tests_empty(self):
        """
        Sprawdza, czy endpoint /tests/ zwraca pustą listę, gdy nie ma plików.
        """
        self.tearDown() # Usuwamy pliki stworzone w setUp
        response = self.client.get('/api/v1/tests/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    # --- Testy dla QuestionListView ---

    def test_get_questions_success(self):
        """
        Sprawdza poprawne pobranie określonej liczby pytań z jednej kategorii.
        """
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_get_questions_from_multiple_categories(self):
        """
        Sprawdza pobranie pytań z wielu kategorii.
        """
        response = self.client.get('/api/v1/questions/', {'categories': 'historia,biologia', 'num_questions': 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_get_questions_missing_params(self):
        """
        Sprawdza, czy brakujące parametry zwracają błąd 400.
        """
        response = self.client.get('/api/v1/questions/')
        self.assertEqual(response.status_code, 400)

    def test_get_questions_more_than_available(self):
        """
        Sprawdza, czy żądanie większej liczby pytań niż dostępna zwraca wszystkie dostępne.
        """
        response = self.client.get('/api/v1/questions/', {'categories': 'biologia', 'num_questions': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2) # W 'biologia.json' są tylko 2 pytania
        
    def test_question_shuffling_logic(self):
        """
        Kluczowy test: Sprawdza, czy po przelosowaniu opcji,
        indeksy 'correctAnswers' nadal wskazują na poprawne odpowiedzi tekstowe.
        """
        # Pobieramy oryginalne dane pytania z wieloma poprawnymi odpowiedziami
        original_question = self.biologia_data['questions'][1] # Pytanie o organella
        original_options = original_question['options']
        original_correct_indices = original_question['correctAnswers']
        original_correct_answers_text = {original_options[i] for i in original_correct_indices}

        # Wykonujemy request
        response = self.client.get('/api/v1/questions/', {'categories': 'biologia', 'num_questions': 2})
        self.assertEqual(response.status_code, 200)
        
        # Znajdujemy nasze pytanie w odpowiedzi (może być na innej pozycji z powodu losowania)
        response_data = response.json()
        shuffled_question = next((q for q in response_data if q['id'] == original_question['id']), None)
        self.assertIsNotNone(shuffled_question)

        # Dodatkowa instrukcja warunkowa, aby pomóc analizatorowi kodu
        if shuffled_question:
            # Sprawdzamy logikę
            shuffled_options = shuffled_question['options']
            shuffled_correct_indices = shuffled_question['correctAnswers']
            shuffled_correct_answers_text = {shuffled_options[i] for i in shuffled_correct_indices}
            
            # Zbiory tekstów poprawnych odpowiedzi (oryginalny i po losowaniu) muszą być identyczne
            self.assertEqual(original_correct_answers_text, shuffled_correct_answers_text)
    
    def test_get_questions_mode_closed_only(self):
        """
        Sprawdza, czy parametr mode='closed' poprawnie filtruje tylko pytania zamknięte.
        """
        # W 'historia.json' mamy 2 pytania zamknięte i 1 otwarte
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 5, 'mode': 'closed'})
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        # Upewniamy się, że żadne z pytań nie jest typu 'open-ended'
        self.assertTrue(all(q['type'] != 'open-ended' for q in response_data))

    def test_get_questions_mode_open_only(self):
        """
        Sprawdza, czy parametr mode='open' poprawnie filtruje tylko pytania otwarte.
        """
        # W 'historia.json' mamy 1 pytanie otwarte
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 5, 'mode': 'open'})
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['type'], 'open-ended')
    
    def test_get_questions_mode_mixed(self):
        """
        Sprawdza, czy domyślny tryb 'mixed' zwraca wszystkie typy pytań.
        """
        # W 'historia.json' są 3 pytania
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 5, 'mode': 'mixed'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_get_questions_invalid_mode(self):
        """
        Sprawdza, czy błędna wartość parametru 'mode' zwraca błąd 400.
        """
        response = self.client.get('/api/v1/questions/', {'categories': 'historia', 'num_questions': 1, 'mode': 'invalid_mode'})
        self.assertEqual(response.status_code, 400)