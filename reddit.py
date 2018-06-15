
# communicate with API
# for the pictures
import hashlib
# config files
import json
import logging
import os
import urllib.parse
# url handler
import urllib.request

import praw

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
# log to file above DEBUG
fileHandler = logging.FileHandler(filename='reddit.log', encoding='utf-8', mode='w')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
# log to console above INFO
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)
# add both
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)


class RedditConfig:
    def __init__(self, configFile):
        with open(configFile) as data_file:
            config_file = json.load(data_file)

        self.client_id = config_file["reddit"]["client_id"]
        self.secret = config_file["reddit"]["secret"]
        self.redirect_uri = config_file["reddit"]["redirect_uri"]
        self.user_agent = config_file["reddit"]["user_agent"]


class Reddit:
    userAgent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"

    def __init__(self, configFile):
        self.config = RedditConfig(configFile)

        self.client = praw.Reddit(client_id=self.config.client_id,
                             client_secret=self.config.secret,
                             redirect_uri=self.config.redirect_uri,
                             user_agent=self.config.user_agent)

        self.alreadyPosted = set()

    def createHash(self, hashThisString):
        md5 = hashlib.md5()
        md5.update(hashThisString.encode('utf-8'))
        return md5.hexdigest()

    def downloadImageFromSubmission(self, submission):
        filename = os.path.join('temp', submission.url.split('/')[-1])

        myopener = urllib.request.build_opener()
        myopener.addheaders = [('User-Agent', self.userAgent)]
        urllib.request.install_opener(myopener)

        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return

        md5 = self.createHash(submission.url)
        if md5 not in self.alreadyPosted:
            try:
                urllib.request.urlretrieve(submission.url, filename)
            except urllib.error.HTTPError:
                logger.warning('Could not download: ', submission.url)

            self.alreadyPosted.add(md5)
            logger.info("New picture found: " + submission.title)

        return filename
