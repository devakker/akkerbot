import os
import unittest

from reddit import Reddit


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.reddit = Reddit('botconfig.json')

    def test_haveConfig(self):
        """
        Test if we have a proper config file
        """
        self.assertNotEqual("", self.reddit.config.client_id)
        self.assertNotEqual("", self.reddit.config.secret)
        self.assertNotEqual("", self.reddit.config.redirect_uri)
        self.assertNotEqual("", self.reddit.config.user_agent)

    def test_configPassed(self):
        """
        Test if we passed the config
        """
        self.assertEqual(self.reddit.config.client_id, self.reddit.client.config.client_id)
        self.assertEqual(self.reddit.config.redirect_uri, self.reddit.client.config.redirect_uri)
        self.assertEqual(self.reddit.config.user_agent, self.reddit.client.config.user_agent)

    def test_haveReddit(self):
        """
        Test if we have a reddit instance
        """
        self.assertTrue(self.reddit.client.read_only)
        # TODO more test


class PostCollectorTestCase(unittest.TestCase):
    def setUp(self):
        self.reddit = Reddit('botconfig.json')
        self.somePost = self.reddit.client.submission(id='8reg0o')

    def test_downloadImageFromSubmission(self):
        self.filename = self.reddit.downloadImageFromSubmission(self.somePost)
        self.assertEqual("temp\\vfvxr2xvd8411.jpg", self.filename)

    def tearDown(self):
        os.remove(self.filename)
