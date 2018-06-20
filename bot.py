# communication with the Discord API
# config files
import asyncio
import json
# obviously logging
import logging
# for the pictures
import os
import hashlib
import urllib.request
# for a lot of things
import random

# for bitcoin
import aiohttp
from discord import Game
from discord.ext import commands
import discord

# my own
from reddit import Reddit

global logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# formatter for both handlers
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
# log to file above DEBUG
fileHandler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
# log to console above INFO
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)
# add both
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

mainLogger = logging.getLogger('discord')
mainLogger.propagate = False
mainLogger.setLevel(logging.DEBUG)
mainLogger.addHandler(fileHandler)
mainLogger.addHandler(consoleHandler)

description = '''Simple bot to post images from reddit automatically.'''
bot = commands.Bot(command_prefix='!', description=description)

user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"


@bot.event
async def on_ready():
    logger.info('Logged into Discord as ' + bot.user.name + " ---- id: " + bot.user.id)
    await bot.change_presence(game=Game(name="with humans"))


@bot.command()
async def bitcoin():
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    async with aiohttp.ClientSession() as session:  # Async HTTP request
        raw_response = await session.get(url)
        response = await raw_response.text()
        response = json.loads(response)
        await bot.say("Bitcoin price is: $" + response['bpi']['USD']['rate'])


@bot.command(name='pics',
             description="Fetches posts containing a single image from reddit.",
             brief="Picture poster",
             aliases=['getpics', 'redditpics'],
             pass_context=True)
async def pics(context, subreddits="pics", limit=5):
    answer_helper = " pictures from **" + subreddits + "**."
    images_posted = await send_pics(limit, context.message.channel, subreddits)
    if images_posted == limit:
        await bot.say(context.message.author.mention + " Found and posted " + str(images_posted) + answer_helper)
    else:
        await bot.say(context.message.author.mention + " Only found " + str(images_posted) + answer_helper)


@bot.command(name='8ball',
             description="Answers a yes/no question.",
             brief="Answers from the beyond.",
             aliases=['eight_ball', 'eightball', '8-ball'],
             pass_context=True)
async def eight_ball(context):
    possible_responses = [
        'That is a resounding no',
        'It is not looking likely',
        'Too hard to tell',
        'It is quite possible',
        'Definitely',
    ]
    question = context.message.author.mention + " asks: " + "**" + context.message.content[7:] + "**"
    answer = "\n ..my answer is: *" + random.choice(possible_responses) + "*"
    await bot.say(question + answer)


@bot.command(name='schedule',
             pass_context=True)
async def schedule_posting_from_reddit(context, which_subs, how_often_in_hours: float, how_many: int = 3):
    await bot.say("I will post **" + str(how_many) + "** pictures from **r/" + which_subs + "** every **" + str(
        how_often_in_hours) + "** hours.")

    bot.loop.create_task(picture_posting_task(subreddits=which_subs, number_of_pictures_to_post=how_many,
                                              target_channel=context.message.channel,
                                              period_in_hours=how_often_in_hours))

    if context.message.channel.id not in PicSender.repost_cache:
        PicSender.repost_cache[context.message.channel.id] = {}


@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user:
        await check_if_repost(message)

    await bot.process_commands(message)


async def check_if_repost(message):
    for attachment in message.attachments:
        if message.channel.id not in PicSender.repost_cache:
            return
        else:
            channel_repost_cache = PicSender.repost_cache[message.channel.id]

        filename = attachment['filename']
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return
        file_path = os.path.join('temp', filename)

        my_opener = urllib.request.build_opener()
        my_opener.addheaders = [('User-Agent', user_agent)]
        urllib.request.install_opener(my_opener)
        urllib.request.urlretrieve(attachment['url'], file_path)

        filename_noextension = filename.split('.')[0]
        filename_hash = hash_string(filename_noextension)
        if filename_hash not in channel_repost_cache:
            channel_repost_cache[filename_hash] = message
            logger.info("Added picture " + filename_noextension + " to reposts in " + message.channel.name)

        os.remove(file_path)


async def picture_posting_task(subreddits, number_of_pictures_to_post, target_channel, period_in_hours):
    if period_in_hours > 0.1:
        period_in_seconds = period_in_hours * 3600
    else:
        period_in_seconds = 360

    await bot.wait_until_ready()
    while not bot.is_closed:
        await send_pics(number_of_pictures_to_post, target_channel, subreddits)
        await asyncio.sleep(period_in_seconds)


async def send_pics(limit, channel, subreddits):
    submissions = reddit.client.subreddit(subreddits).hot(limit=50)
    images_posted = 0
    for submission in submissions:
        if channel.id not in PicSender.repost_cache:
            PicSender.repost_cache[channel.id] = {}
        filename = submission.url.split('/')[-1].split('.')[0]
        if hash_string(filename) in PicSender.repost_cache[channel.id]:
            continue

        file_path = reddit.downloadImageFromSubmission(submission)
        if not file_path:
            continue
        pic_sender = PicSender(file_path)
        try:
            await pic_sender.send(channel)
        except RuntimeError:
            images_posted = images_posted - 1

        os.remove(file_path)
        images_posted = images_posted + 1
        if images_posted == limit:
            break
    return images_posted


def hash_string(hashThisString):
    md5 = hashlib.md5()
    md5.update(hashThisString.encode('utf-8'))
    return md5.hexdigest()


class PicSender:
    repost_cache = {}

    def __init__(self, file_path):
        self.file_path = file_path

        filename = file_path.split('\\')[-1].split('.')[0]
        self.hash_of_filename = hash_string(filename)

    async def send(self, target_channel: discord.Channel):
        if target_channel.id in PicSender.repost_cache:
            channel_repost_cache = PicSender.repost_cache[target_channel.id]
            if self.hash_of_filename in channel_repost_cache:
                raise RuntimeError('repost, did not send')
            else:
                message = await bot.send_file(target_channel, self.file_path)
                channel_repost_cache[self.hash_of_filename] = message
        else:
            await bot.send_file(target_channel, self.file_path)


global reddit
reddit = Reddit()

bot.run(os.environ['discordToken'])
