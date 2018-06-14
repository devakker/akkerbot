import unittest

from reddit import Reddit


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.reddit = Reddit('botconfig.json')

    def test_haveConfig(self):
        self.assertNotEqual(self.reddit.config.client_id, "")
        self.assertNotEqual(self.reddit.config.secret, "")
        self.assertNotEqual(self.reddit.config.redirect_uri, "")
        self.assertNotEqual(self.reddit.config.user_agent, "")

    def test_haveReddit(self):
        self.assertTrue(self.reddit.client.read_only)
