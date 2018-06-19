
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
             aliases=['getpics','redditpics'],
             pass_context=True)
async def pics(context, subreddits="pics", limit=5):
    answerHelper = " pictures from **" + subreddits + "**."
    imagesPosted = await send_pics(limit, context.message.channel, subreddits)
    if imagesPosted == limit:
        await bot.say(context.message.author.mention + " Found and posted " + str(imagesPosted) + answerHelper)
    else:
        await bot.say(context.message.author.mention + " Only found " + str(imagesPosted) + answerHelper)


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
async def schedule_posting_from_reddit(context, which_subs, how_often_in_hours:float, how_many:int = 3):
    bot.loop.create_task(picture_posting_task(subreddits=which_subs, number_of_pictures_to_post=how_many,
                                              target_channel=context.message.channel, period_in_hours=how_often_in_hours))
    if context.message.channel.id not in PicSender.repost_cache:
        PicSender.repost_cache[context.message.channel.id] = {}


@bot.event
async def check_if_repost(message):
    if message.channel.id not in PicSender.repost_cache:
        return
    else:
        channel_repost_cache = PicSender.repost_cache[message.channel.id]

    if message.author == bot.user:
        return

    for attachment in message.attachments:
        if not attachment['filename'].lower().endswith(('.png', '.jpg', '.jpeg')):
            return
        file_path = os.path.join('temp', attachment['filename'])

        myopener = urllib.request.build_opener()
        myopener.addheaders = [('User-Agent', user_agent)]
        urllib.request.install_opener(myopener)
        urllib.request.urlretrieve(attachment['url'], file_path)

        file_hash = hash_file(file_path)
        if file_hash not in channel_repost_cache:
            channel_repost_cache[file_hash] = message

        os.remove(file_path)


@bot.event
async def on_message(message: discord.Message):
    await check_if_repost(message)
    await bot.process_commands(message)


async def send_pics(limit, channel, subreddits):
    submissions = reddit.client.subreddit(subreddits).hot(limit=50)
    images_posted = 0
    for submission in submissions:
        file_path = reddit.downloadImageFromSubmission(submission)
        if file_path:
            if channel.id not in PicSender.repost_cache:
                PicSender.repost_cache[channel.id] = {}
            picSender = PicSender(file_path)
            try:
                await picSender.send(channel)
            except RuntimeError:
                images_posted = images_posted - 1
            os.remove(file_path)
            images_posted = images_posted + 1
        if images_posted == limit:
            break
    return images_posted


async def picture_posting_task(subreddits, number_of_pictures_to_post, target_channel, period_in_hours):
    if period_in_hours > 0.1:
        period_in_seconds = period_in_hours * 3600
    else:
        period_in_seconds = 360

    await bot.wait_until_ready()
    while not bot.is_closed:
        await send_pics(number_of_pictures_to_post, target_channel, subreddits)
        await asyncio.sleep(period_in_seconds)


def hash_file(file_path):
    buf_size = 65536  # lets read stuff in 64kb chunks!
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


class PicSender:
    repost_cache = {}

    def __init__(self, file_path):
        self.file_path = file_path
        self.hash_of_image = hash_file(file_path)

    async def send(self, target_channel: discord.Channel):
        if target_channel.id in self.repost_cache:
            channel_repost_cache = self.repost_cache[target_channel.id]
            if self.hash_of_image in channel_repost_cache:
                raise RuntimeError('repost, did not send')
            else:
                message = bot.send_file(target_channel, self.file_path)
                await message
                channel_repost_cache[self.hash_of_image] = message
        else:
            await bot.send_file(target_channel, self.file_path)


global reddit
reddit = Reddit()

bot.run(os.environ['discordToken'])
