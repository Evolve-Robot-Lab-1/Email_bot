import unittest
from unittest.mock import patch, MagicMock
from src.email_full_integ import gmail_authenticate, read_emails, send_email, reply_email, manage_labels, delete_email

class TestEmailIntegration(unittest.TestCase):

    @patch('src.email_full_integ.build')
    def test_gmail_authenticate(self, mock_build):
        mock_creds = MagicMock()
        mock_build.return_value = mock_creds
        service = gmail_authenticate()
        self.assertEqual(service, mock_creds)

    @patch('src.email_full_integ.service.users().messages().list')
    def test_read_emails(self, mock_list):
        mock_list.return_value.execute.return_value = {'messages': [{'id': '123'}]}
        service = MagicMock()
        service.users().messages().list.return_value = mock_list
        with patch('builtins.print') as mocked_print:
            read_emails(service)
            mocked_print.assert_called_with("\n📩 Latest Emails:\nFrom: (No Sender)\nSubject: (No Subject)\nSnippet: \nMessage ID: 123\n")

    @patch('src.email_full_integ.service.users().messages().send')
    def test_send_email(self, mock_send):
        mock_send.return_value.execute.return_value = {'id': '456'}
        service = MagicMock()
        with patch('builtins.input', side_effect=['test@example.com', 'Test Subject', 'Test Body']):
            with patch('builtins.print') as mocked_print:
                send_email(service)
                mocked_print.assert_called_with("\n✅ Email sent successfully! Message ID: 456")

    @patch('src.email_full_integ.service.users().messages().send')
    def test_reply_email(self, mock_send):
        mock_send.return_value.execute.return_value = {'id': '789'}
        service = MagicMock()
        with patch('builtins.input', side_effect=['123', 'Test Reply']):
            with patch('builtins.print') as mocked_print:
                reply_email(service)
                mocked_print.assert_called_with("\n📨 Reply sent successfully! Message ID: 789")

    @patch('src.email_full_integ.service.users().labels().list')
    def test_manage_labels_list(self, mock_list):
        mock_list.return_value.execute.return_value = {'labels': [{'name': 'Test Label', 'id': '1'}]}
        service = MagicMock()
        with patch('builtins.print') as mocked_print:
            manage_labels(service)
            mocked_print.assert_called_with("\nAvailable Labels:\n- Test Label (ID: 1)")

    @patch('src.email_full_integ.service.users().messages().delete')
    def test_delete_email(self, mock_delete):
        service = MagicMock()
        with patch('builtins.input', side_effect=['123']):
            with patch('builtins.print') as mocked_print:
                delete_email(service)
                mocked_print.assert_called_with("🗑️ Email deleted successfully!")

if __name__ == '__main__':
    unittest.main()