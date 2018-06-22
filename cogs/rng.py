
import random
from discord.ext import commands


class RNG:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, dice: str):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await self.bot.say('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await self.bot.say(result)

    @commands.command()
    async def choose(self, *choices: str):
        """Chooses between multiple choices.
        For when you wanna settle the score some other way'
        """
        await self.bot.say(random.choice(choices))

    @commands.command(name='8ball', pass_context=True)
    async def eight_ball(self, context):
        """Answers from beyond.
        Answers a yes/no question.
        """
        possible_responses = [
            'That is a resounding no',
            'It is not looking likely',
            'Too hard to tell',
            'It is quite possible',
            'Definitely',
        ]
        question = context.message.author.mention + " asks: " + "**" + context.message.content[7:] + "**"
        answer = "\n ..my answer is: *" + random.choice(possible_responses) + "*"
        await self.bot.say(question + answer)


def setup(bot):
    bot.add_cog(RNG(bot))
