import discord
from discord.ext import commands

# communicate with API
import praw
# path handling
import os
# downloading files
import urllib.parse
import urllib.request
import logging
# scheduling
import asyncio


class Pics:
    repost_cache = {}
    user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"

    logger = logging.getLogger('akkerbot')

    def __init__(self, bot):
        self.bot = bot
        self.redditClient = praw.Reddit(client_id=os.environ['reddit_clientID'],
                                        client_secret=os.environ['reddit_clientSecret'],
                                        redirect_uri="http://localhost:8080",
                                        user_agent="dumbot (by /u/spinakkerDota)")

    @commands.command(aliases=['getpics', 'redditpics'], pass_context=True)
    async def pics(self, context, subreddits="pics", limit=5):
        """Posts images from subreddits.
        Fetches posts directly linking to images from subreddits.
        You can combine subs too: awww+eyebleach"""
        answer_helper = " pictures from **" + subreddits + "**."
        images_posted = await self.send_pics(limit, context.message.channel, subreddits)
        if images_posted == limit:
            await self.bot.say(
                context.message.author.mention + " Found and posted " + str(images_posted) + answer_helper)
        else:
            await self.bot.say(context.message.author.mention + " Only found " + str(images_posted) + answer_helper)

    @commands.command(name='schedule', pass_context=True)
    async def schedule_posting_from_reddit(self, context, which_subs, how_often_in_hours: float, how_many: int = 3):
        """Posts pictures from subreddits every x hours.
        You can use periods like 0.11 hours, but 0.1 is the minimum"""
        await self.bot.say("I will post **" + str(how_many) + "** pictures from **r/" +
                           which_subs + "** every **" + str(how_often_in_hours) + "** hours.")
        self.bot.loop.create_task(self.picture_posting_task(subreddits=which_subs, number_of_pictures_to_post=how_many,
                                                            target_channel=context.message.channel,
                                                            period_in_hours=how_often_in_hours))

    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            self.check_if_repost(message)

    async def picture_posting_task(self, subreddits, number_of_pictures_to_post, target_channel, period_in_hours):
        if period_in_hours > 0.1:
            period_in_seconds = period_in_hours * 3600
        else:
            period_in_seconds = 360

        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            await self.send_pics(number_of_pictures_to_post, target_channel, subreddits)
            await asyncio.sleep(period_in_seconds)

    async def send_pics(self, limit, channel, subreddits):
        submissions = self.redditClient.subreddit(subreddits).hot(limit=50)
        images_posted = 0
        for submission in submissions:
            channel_repost_cache = {} #TODO is this needed?
            if channel.id in self.repost_cache:
                channel_repost_cache = self.repost_cache[channel.id]
            else:
                self.repost_cache[channel.id] = channel_repost_cache
            filename = submission.url.split('/')[-1].split('.')[0]
            if filename in channel_repost_cache:
                continue

            file_path = self.download_image_from_submission(submission)
            if not file_path:
                continue

            message = await self.bot.send_file(channel, file_path)
            channel_repost_cache[filename] = message

            os.remove(file_path)
            images_posted = images_posted + 1
            if images_posted == limit:
                break
        return images_posted

    def download_image_from_submission(self, submission):
        file_path = os.path.join('temp', submission.url.split('/')[-1])

        myopener = urllib.request.build_opener()
        myopener.addheaders = [('User-Agent', self.user_agent)]
        urllib.request.install_opener(myopener)

        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return

        try:
            urllib.request.urlretrieve(submission.url, file_path)
        except urllib.error.HTTPError:
            self.logger.warning('Could not download: ', submission.url)

        self.logger.info("New picture found: " + submission.title)
        return file_path

    def check_if_repost(self, message: discord.Message):
        for attachment in message.attachments:
            if message.channel.id not in self.repost_cache:
                return
            else:
                channel_repost_cache = self.repost_cache[message.channel.id]

            filename = attachment['filename']
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return
            file_path = os.path.join('temp', filename)

            my_opener = urllib.request.build_opener()
            my_opener.addheaders = [('User-Agent', self.user_agent)]
            urllib.request.install_opener(my_opener)
            urllib.request.urlretrieve(attachment['url'], file_path)

            filename_noextension = filename.split('.')[0]
            if filename_noextension not in channel_repost_cache:
                channel_repost_cache[filename_noextension] = message
                self.logger.info("Added picture " + filename_noextension + " to reposts in " + message.channel.name)

            os.remove(file_path)


def setup(bot):
    bot.add_cog(Pics(bot))
