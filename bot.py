
# communication with the Discord API
# config files
import json
# obviously logging
import logging
# for the pictures
import os
# for a lot of things
import random

# for bitcoin
import aiohttp
from discord import Game
from discord.ext import commands

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

alreadyPosted = set()

user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"

with open('botconfig.json') as data_file:
    config_file = json.load(data_file)

global discordToken
discordToken = config_file["discord"]["token"]

### here we go
global reddit
reddit = Reddit('botconfig.json')
bot.run(discordToken)


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

    submissions = reddit.client.subreddit(subreddits).hot(limit=50)
    imagesPosted = 0
    for submission in submissions:
        filename = reddit.downloadImageFromSubmission(submission)
        if filename:
            await bot.send_file(context.message.channel, filename)
            os.remove(filename)
            imagesPosted = imagesPosted + 1
        if imagesPosted == limit:
            await bot.say(context.message.author.mention + " Found and posted " + str(imagesPosted) + answerHelper)
            return
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



