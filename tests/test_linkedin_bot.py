import unittest
from unittest.mock import patch, MagicMock
from linkedin_bot import LinkedInAPI, LMStudioInterface, LinkedInBot

class TestLinkedInAPI(unittest.TestCase):
    @patch("requests.post")
    def test_authenticate(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_at": 9999999999
        }
        mock_post.return_value = mock_response
        
        api = LinkedInAPI("client_id", "client_secret", "http://localhost:8000/callback")
        self.assertTrue(api.authenticate("test_code"))
        self.assertEqual(api.access_token, "test_token")
    
    @patch("requests.get")
    def test_get_current_user_profile(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "id": "12345",
            "firstName": "John",
            "lastName": "Doe"
        }
        api = LinkedInAPI("client_id", "client_secret", "http://localhost:8000/callback")
        api.access_token = "test_token"
        profile = api.get_current_user_profile()
        self.assertEqual(profile["firstName"], "John")
        self.assertEqual(profile["lastName"], "Doe")


class TestLMStudioInterface(unittest.TestCase):
    @patch("requests.post")
    def test_generate_message(self, mock_post):
        # Simulamos una respuesta exitosa de LM Studio
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [
                {"message": {"content": "Hello Recruiter!"}}
            ]
        }

        lm_studio = LMStudioInterface()
        message = lm_studio.generate_message(
            "Hello {recruiter_name}",
            {"recruiter_name": "John"}
        )
        self.assertIn("Hello Recruiter", message)


class TestLinkedInBot(unittest.TestCase):
    @patch.object(LinkedInAPI, "filter_recruiter_connections", return_value=[
        {"id": "1", "firstName": "Jane", "title": "Recruiter"}
    ])
    @patch.object(LinkedInAPI, "send_message", return_value=True)
    def test_contact_recruiters(self, mock_send_message, mock_filter_recruiters):
        api = LinkedInAPI("client_id", "client_secret", "http://localhost:8000/callback")
        lm_studio = LMStudioInterface()
        bot = LinkedInBot(api, lm_studio)

        # Simulamos que el bot está autenticado
        bot.user_profile = {"firstName": "John", "lastName": "Doe"}
        
        results = bot.contact_recruiters()
        self.assertEqual(results["success"], 1)
        self.assertEqual(results["failed"], 0)


if __name__ == "__main__":
    unittest.main()
