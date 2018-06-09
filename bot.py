
# communication with the Discord API
from discord.ext import commands
from discord import Game

# communicate with Reddit API
import praw

# config files
import json

# url handler
import urllib.request
import urllib.parse

# for the pictures
import hashlib
import sys
import os
import errno

# for bitcoin
import aiohttp

# for a lot of things
import random


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

ERROR_INVALID_NAME = 123
def is_pathname_valid(pathname: str) -> bool:

    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        _, pathname = os.path.splitdrive(pathname)
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)

            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False

    except TypeError as exc:
        return False

    else:
        return True


def initializeConfig():
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
    print("Fetching " + str(picLimit) + " pictures from " + subs)

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

        if not is_pathname_valid(filename):
            continue

        md5 = createHash(submission.url)
        if md5 not in alreadyPosted:
            try:
                urllib.request.urlretrieve(submission.url, filename)
            except urllib.error.HTTPError:
                print ('Could not download: ', submission.url)

            alreadyPosted.add (md5)
            print("New picture found: " + submission.title)
            numberOfPicsFound = numberOfPicsFound + 1
            fileNames.append (filename)

        if numberOfPicsFound == picLimit:
            break

    if numberOfPicsFound != picLimit:
        print("Only found " + str(numberOfPicsFound) + " pictures.")
        # let the caller know especially if 0

    return fileNames


@bot.event
async def on_ready():
    print('Logged into Discord as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.change_presence(game=Game(name="with humans"))


@bot.command()
async def bitcoin():
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    async with aiohttp.ClientSession() as session:  # Async HTTP request
        raw_response = await session.get(url)
        response = await raw_response.text()
        response = json.loads(response)
        await bot.say("Bitcoin price is: $" + response['bpi']['USD']['rate'])


@bot.command(pass_context=True)
async def pics(ctx, subreddits = "pics", limit = 5):
    fileNames = getPicsFromReddit(subreddits, limit)

    for filename in fileNames:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            print("Sending picture " + filename +"..")

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
    await bot.say(random.choice(possible_responses) + ", " + context.message.author.mention)


@bot.event
async def on_command_completion(command, ctx):
    await bot.delete_message(ctx.message)


### here we go

initializeConfig()

reddit = praw.Reddit(client_id=RedditConfigData.client_id,
                     client_secret=RedditConfigData.secret,
                     redirect_uri=RedditConfigData.redirect_uri,
                     user_agent=RedditConfigData.user_agent)

bot.run(discordToken)
