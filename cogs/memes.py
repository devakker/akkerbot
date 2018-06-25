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

    @commands.command(pass_context=True)
    async def meme(self, context, name):
        target_channel = context.message.channel
        if name in self.memes:
            file_path = self.memes[name]
        else:
            await self.bot.say(f"That meme doesn't exist. Perhaps you should add it!")
            return

        await self.bot.send_file(target_channel, file_path)

    @commands.command(name='addmeme', pass_context=True)
    async def add(self, context, name):
        if name in self.memes:
            await self.bot.say(f"Meme with the name **{name}** already exists.")
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

    @commands.command(name= 'removememe', pass_context=True)
    async def remove(self, context, name):
        if name in self.memes:
            os.remove(self.memes[name])
            del self.memes[name]
            await self.bot.say(f"Deleted the meme.")
        else:
            await self.bot.say(f"That meme doesn't exist. Perhaps you should add it!")

    @commands.command(name='listmemes', pass_context=True)
    async def list(self, context):
        if not self.memes:
            await self.bot.say(f"No memes have been added yet.")
            return
        response = '**Memes:** '
        for name in self.memes:
            response = response + f'{name}, '
        await self.bot.say(response)


def setup(bot):
    bot.add_cog(Memes(bot))
