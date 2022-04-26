import asyncio # noqa
import discord # noqa
from discord.ext import commands
import time

MYID = 592895305125593228


intents = discord.Intents.default()
intents.members = True


class Unanimism(commands.Bot):
    """Unanimism \\ yüˈnanəˌmizəm \\ noun: unifying principles are more significant than personal individualities."""

    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)

    def log_message(self, message):
        print(f'[{time.ctime()}] {message.author.name} - {message.guild} #{message.channel}: {message.content}')

    async def process_commands(self, message):
        """Process the commands for a message."""
        if message.author.bot:
            if message.author.id == MYID:
                self.log_message(message)
            return

        ctx = await self.get_context(message)
        if ctx.prefix:
            self.log_message(message)
        await self.invoke(ctx)

    async def on_message(self, message):
        """Handle received messages."""
        await self.process_commands(message)

    async def on_ready(self):
        print(f'Logged into {len(self.guilds)} guilds:')
        for guild in list(self.guilds):
            print(f'\t{guild.name}:{guild.id}')
        print("Ready to democracy.")


if __name__ == '__main__':
    with open('secret') as f:
        secret = f.read()
    bot = Unanimism(command_prefix=commands.when_mentioned_or('u.'), intents=intents)
    bot.load_extension('polls')
    bot.load_extension('presence')

    @commands.is_owner()
    @bot.command(hidden=True)
    async def reload(ctx):
        await bot.get_cog('Polls').cleanup()
        await ctx.send('Reloading ' + ', '.join([(str(x)) for x in bot.extensions]))
        for ext in bot.extensions:
            bot.reload_extension(ext)

    bot.run(secret)
