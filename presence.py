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
        self.task_change_presence.start()

    def cog_unload(self):
        self.task_change_presence.cancel()

    @tasks.loop(seconds=20)
    async def task_change_presence(self):
        if not self.bot.is_closed():
            curr = next(self.presences)
            await self.bot.change_presence(activity=discord.Activity(
                type=curr[0], name=curr[1]
            ))

    @task_change_presence.before_loop
    async def task_before_change_presence(self):
        await self.bot.wait_until_ready()
