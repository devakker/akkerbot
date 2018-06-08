
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

import hashlib
import sys
import os
import errno

import aiohttp


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
    '''
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    '''
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError as exc:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.
    #
    # Did we mention this should be shipped with Python already?


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
