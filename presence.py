import asyncio
from itertools import cycle
import discord
from discord.enums import ActivityType
from discord.ext import commands, tasks

PRESENCES = [(ActivityType.watching,  'for u.help or u.poll'),
             (ActivityType.playing,   'Democracy'),
             (ActivityType.watching,  'for u.help or u.poll'),
             (ActivityType.listening, 'your complaints'),
            ]

def setup(bot):
    bot.add_cog(Presence(bot))


class Presence(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.presences = cycle(PRESENCES)
        self.change_presence_task.start()

    def cog_unload(self):
        self.change_presence_task.cancel()

    @tasks.loop(seconds=20)
    async def change_presence_task(self):
        if not self.bot.is_closed():
            curr = next(self.presences)
            await self.bot.change_presence(activity=discord.Activity(
                type=curr[0], name=curr[1]
            ))

    @change_presence_task.before_loop
    async def before_presence_task(self):
        await self.bot.wait_until_ready()
