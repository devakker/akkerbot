
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


# communicate with Reddit API
# url handler


def initLogging():
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


class RedditConfigData:
    client_id = ""
    secret = ""
    redirect_uri = ""
    user_agent = ""


discordToken = ""

description = '''Simple bot to post images from reddit automatically.'''
bot = commands.Bot(command_prefix='!', description=description)

alreadyPosted = set()

user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"

def readConfig():
    with open('botconfig.json') as data_file:
        config_file = json.load(data_file)

    global discordToken
    discordToken = config_file["discord"]["token"]

    RedditConfigData.client_id = config_file["reddit"]["client_id"]
    RedditConfigData.secret = config_file["reddit"]["secret"]
    RedditConfigData.redirect_uri = config_file["reddit"]["redirect_uri"]
    RedditConfigData.user_agent = config_file["reddit"]["user_agent"]


def createSuperSub():
    with open("sublist.json") as data_file:
        configData = json.load(data_file)
    combinedSubname = "\'"
    for i in configData["subs"]:
        combinedSubname += (i["name"]) + "+"
    combinedSubname = combinedSubname[:-1]
    combinedSubname += '\''
    return combinedSubname


def createHash(hashThisString):

    md5 = hashlib.md5()
    md5.update(hashThisString.encode('utf-8'))
    return md5.hexdigest()


def getPicsFromReddit(subs, picLimit):
    myLogger.info("Fetching " + str(picLimit) + " pictures from " + subs)

    submissions = reddit.subreddit(subs).hot(limit = 50)

    numberOfPicsFound = 0
    fileNames = []
    for submission in submissions:

        filename = os.path.join('temp', submission.url.split('/')[-1])

        myopener = urllib.request.build_opener()
        myopener.addheaders = [('User-Agent', user_agent)]
        urllib.request.install_opener(myopener)

        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        md5 = createHash(submission.url)
        if md5 not in alreadyPosted:
            try:
                urllib.request.urlretrieve(submission.url, filename)
            except urllib.error.HTTPError:
                myLogger.warning ('Could not download: ', submission.url)

            alreadyPosted.add (md5)
            myLogger.info("New picture found: " + submission.title)
            numberOfPicsFound = numberOfPicsFound + 1
            fileNames.append (filename)

        if numberOfPicsFound == picLimit:
            break

    if numberOfPicsFound != picLimit:
        myLogger.warning("Only found " + str(numberOfPicsFound) + " pictures.")
        # let the caller know especially if 0

    return fileNames


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
async def pics(ctx, subreddits = "pics", limit = 5):
    fileNames = getPicsFromReddit(subreddits, limit)

    for filename in fileNames:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            myLogger.info("Sending picture " + filename +"..")

            await bot.send_file(ctx.message.channel, filename)
            os.remove(filename)


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


@bot.event
async def on_command_completion(command, ctx):
    await bot.delete_message(ctx.message)


### here we go

readConfig()
initLogging()


bot.run(discordToken)
