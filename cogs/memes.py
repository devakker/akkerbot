import discord
from discord.ext import commands
import logging

import os.path
from utils import download_image_from_url


class Memes:
    logger = logging.getLogger('akkerbot')
    memes = {}

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='addmeme', pass_context=True)
    async def add(self, context, name):
        if name in self.memes:
            self.bot.say(f"Meme with the name **{name}** already exists.")
            return

        message: discord.Message = context.message
        for attachment in message.attachments:
            filename = attachment['filename']
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return

            old_name, file_extension = os.path.splitext(filename)
            file_path = os.path.join('memes', name + file_extension)
            url = attachment['url']
            try:
                await download_image_from_url(url, file_path)
            except:
                await self.bot.say("Something is wrong with that meme :(")

            self.memes[name] = file_path
            await self.bot.say(f"Meme added as **{name}**.")

    @commands.command(pass_context=True)
    async def meme(self, context, name):
        target_channel = context.message.channel
        if name in self.memes:
            file_path = self.memes[name]
        else:
            await self.bot.say("I don't know that meme :(")
            return

        author:discord.Member = context.message.author
        if author.id != '79555854818357248':
            await self.bot.send_file(target_channel, file_path)
        else:
            await self.bot.send_file(target_channel, os.path.join('memes', 'humpgnome.png'))

def setup(bot):
    bot.add_cog(Memes(bot))
