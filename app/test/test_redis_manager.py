import unittest
import fakeredis
from langchain_core.messages import BaseMessage, HumanMessage
from app.database.redis_server import RedisChatMessageHistor

class TestRedisChatMessageHistor(unittest.TestCase):
    def setUp(self):
        self.fake_redis = fakeredis.FakeRedis(decode_responses=True)
        self.session_id = "test_session"
        self.user_id = "test_user"
        self.chat = RedisChatMessageHistor(
            session_id=self.session_id,
            user_id=self.user_id,
            redis_url=None
        )
        # Patch the _client to use fake redis
        self.chat._client = self.fake_redis

    def test_add_and_load_messages(self):
        msg = HumanMessage(content="Hello!")
        self.chat.add_messages(msg)
        messages = self.chat.messages()
        self.assertEqual(messages[0].content, "Hello!")

    def test_clear(self):
        msg = HumanMessage(content="Bye!")
        self.chat.add_messages(msg)
        self.chat.clear()
        messages = self.chat.messages()
        self.assertEqual(len(messages), 0)

if __name__ == "__main__":
    unittest.main()