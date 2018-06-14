
# communicate with API
import praw

# config files
import json


class RedditConfig:

    def __init__(self, configFile):
        with open(configFile) as data_file:
            config_file = json.load(data_file)

        self.client_id = config_file["reddit"]["client_id"]
        self.secret = config_file["reddit"]["secret"]
        self.redirect_uri = config_file["reddit"]["redirect_uri"]
        self.user_agent = config_file["reddit"]["user_agent"]


class Reddit:
    def __init__(self, configFile):
        self.config = RedditConfig(configFile)

        self.client = praw.Reddit(client_id=self.config.client_id,
                             client_secret=self.config.secret,
                             redirect_uri=self.config.redirect_uri,
                             user_agent=self.config.user_agent)

    def collectURLs(self, sub, sorting = 'hot', time='alltime', limit=50):
        if limit > 50:
            limit = 50

        if (sorting == 'hot'):
            submissions = self.client.subreddit(sub).hot(limit=limit)
        else:
            submissions = self.client.subreddit(sub).top(limit=limit, time_filter=time)

        postURLs = []
        for submission in submissions:
            postURLs.append(submission.url)

        return postURLs
