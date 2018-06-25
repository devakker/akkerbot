import discord
from discord.ext import commands
import logging

# communicate with API
import praw
# path handling
import os
# scheduling
import asyncio
import datetime
# download images
from utils import download_image_from_url


class Pics:
    repost_cache = {}
    tasks = {}

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
        images_posted = await self.post_pictures_from_reddit(limit, context.message.channel, subreddits)
        if images_posted == limit:
            await self.bot.say(
                context.message.author.mention + " Found and posted " + str(images_posted) + answer_helper)
        else:
            await self.bot.say(context.message.author.mention + " Only found " + str(images_posted) + answer_helper)

    @commands.command(name='schedule', pass_context=True)
    async def schedule_posting_from_reddit(self, context, which_subs, how_often_in_hours: float, how_many: int = 3):
        """Posts pictures from subreddits every x hours.
        You can use periods like 0.11 hours, but 0.1 is the minimum"""
        author = context.message.author
        channel_id = context.message.channel.id
        if channel_id not in self.tasks:
            self.tasks[channel_id] = {}

        if author not in self.tasks[channel_id]:
            self.tasks[channel_id][author] = []

        maximum_tasks_per_user = 5
        if len(self.tasks[channel_id][author]) >= maximum_tasks_per_user:
            await self.bot.say(f'You have exceeded the max amount of tasks you can set '
                               f'in this channel ({maximum_tasks_per_user}).')
            return

        task = self.bot.loop.create_task(
            self.picture_posting_task(subreddits=which_subs, number_of_pictures_to_post=how_many,
                                      target_channel=context.message.channel,
                                      period_in_hours=how_often_in_hours))
        task.owner = author
        task.channel = context.message.channel
        task.subs = which_subs
        task.limit = how_many
        task.period = how_often_in_hours

        self.tasks[channel_id][task.owner].append(task)
        await self.bot.say(
            f"I will post **{how_many}** picture(s) from **r/{which_subs}** every **{how_often_in_hours}** hours.")

    # TODO description
    @commands.command(name='mytasks', pass_context=True)
    async def list_users_running_tasks(self, context):
        channel_id = context.message.channel.id
        if channel_id not in self.tasks:
            await self.bot.say("No tasks running in this channel.")
            return
        author = context.message.author
        if author not in self.tasks[channel_id]:
            await self.bot.say("You have no tasks running in this channel.")
            return
        user_tasks = self.tasks[channel_id][author]
        if not user_tasks:
            await self.bot.say("You have no tasks running in this channel.")
            return

        embed = discord.Embed(title=f'{author}''s tasks running in this channel:', colour=discord.Colour(0xd000e6),
                              timestamp=datetime.datetime.utcfromtimestamp(1529866412))
        embed.set_footer(text=self.bot.user.name)
        index_field_helper = ''
        sub_field_helper = ''
        limit_field_helper = ''
        period_field_helper = ''
        for index, task in enumerate(user_tasks):
            index_field_helper = index_field_helper + f'{index}\n'
            sub_field_helper = sub_field_helper + f'{task.subs}\n'
            limit_field_helper = limit_field_helper + f'{task.limit}\n'
            period_field_helper = period_field_helper + f'{task.period}\n'
        embed.add_field(name='Index', value=index_field_helper, inline=True)
        embed.add_field(name='Subreddits', value=sub_field_helper, inline=True)
        embed.add_field(name='Limit', value=limit_field_helper, inline=True)
        embed.add_field(name='Period', value=period_field_helper, inline=True)
        await self.bot.say(embed=embed)

    # TODO description
    # TODO some code duplication here, should put task handling into a separate module
    @commands.command(name='removetask', pass_context=True)
    async def remove_user_task(self, context, task_index: int):
        channel_id = context.message.channel.id
        if channel_id not in self.tasks:
            await self.bot.say("No tasks running in this channel.")
            return
        author = context.message.author
        if author not in self.tasks[channel_id]:
            await self.bot.say("You have no tasks running in this channel.")
            return
        user_tasks = self.tasks[channel_id][author]
        try:
            del user_tasks[task_index]
        except IndexError:
            await self.bot.say(f'No task with that index.')
            return
        await self.bot.say(f'Deleted task with index {task_index}.')

    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            await self.check_if_repost(message)

    async def picture_posting_task(self, subreddits, number_of_pictures_to_post, target_channel, period_in_hours):
        if period_in_hours > 0.1:
            period_in_seconds = period_in_hours * 3600
        else:
            period_in_seconds = 360

        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            await self.post_pictures_from_reddit(number_of_pictures_to_post, target_channel, subreddits)
            await asyncio.sleep(period_in_seconds)

    async def post_pictures_from_reddit(self, limit, channel, subreddits):
        submissions = self.redditClient.subreddit(subreddits).hot(limit=50)
        number_of_images_posted = 0
        for submission in submissions:
            if channel.id not in self.repost_cache:
                self.repost_cache[channel.id] = {}
            channel_repost_cache = self.repost_cache[channel.id]

            url = submission.url
            if not url.lower().endswith(('.png', '.jpg', '.jpeg')):
                return

            filename_no_extension = url.split('/')[-1].split('.')[0]
            if filename_no_extension in channel_repost_cache:
                continue

            file_path = os.path.join('temp', url.split('/')[-1])
            try:
                await download_image_from_url(url, file_path)
            except:  # TODO find what errors can this throw
                continue

            self.logger.info(f'New picture found: {submission.title}')

            message = await self.bot.send_file(channel, file_path)
            channel_repost_cache[filename_no_extension] = message

            os.remove(file_path)
            number_of_images_posted = number_of_images_posted + 1
            if number_of_images_posted == limit:
                break
        return number_of_images_posted

    # TODO this could be placed in an utils file

    async def check_if_repost(self, message: discord.Message):
        for attachment in message.attachments:
            if message.channel.id not in self.repost_cache:
                return
            else:
                channel_repost_cache = self.repost_cache[message.channel.id]

            filename = attachment['filename']
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return

            file_path = os.path.join('temp', filename)
            url = attachment['url']
            try:
                await download_image_from_url(url, file_path)
            except:  # TODO find what errors can this throw
                continue

            filename_no_extension = filename.split('.')[0]
            if filename_no_extension not in channel_repost_cache:
                channel_repost_cache[filename_no_extension] = message
                self.logger.info(f"Added picture {filename_no_extension} to reposts in {message.channel.name}")

            os.remove(file_path)


def setup(bot):
    bot.add_cog(Pics(bot))
