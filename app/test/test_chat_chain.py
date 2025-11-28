import unittest
from unittest.mock import MagicMock, patch

from app.chains.chat_chain import Chat


class TestChatChain(unittest.TestCase):
    def setUp(self):
        self.chat = Chat(session_id="sess-1", user_id="user-1", page_url="https://example.com", query="hi")

    @patch("app.chains.chat_chain.RunnableWithMessageHistory")
    def test_run_invokes_chain_with_expected_payload(self, mock_runnable_cls):
        prompt_mock = MagicMock()
        model_mock = MagicMock()
        parser_mock = MagicMock()
        chain_mock = MagicMock()
        mock_runnable_cls.return_value = chain_mock
        chain_mock.invoke.return_value = "final-response"

        with patch.object(self.chat, "get_prompt_template", return_value=prompt_mock), \
             patch.object(self.chat, "get_model", return_value=model_mock), \
             patch.object(self.chat, "get_context_documents", return_value="ctx"), \
             patch("app.chains.chat_chain.StrOutputParser", return_value=parser_mock), \
             patch.object(self.chat, "get_history_factory", return_value=lambda session: MagicMock()):
            result = self.chat.run(query="hello world")

        self.assertEqual(result, "final-response")
        expected_vars = {"context": "ctx", "input": "hello world"}
        chain_mock.invoke.assert_called_once_with(expected_vars)


if __name__ == "__main__":
    unittest.main()