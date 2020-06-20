import asyncio
import discord
from discord.ext import commands
from importlib import reload
import pickle
import poll
from poll import Poll, Voter
from typing import Dict, Optional, Set, Union

ALPHAMOJI = ['regional_indicator_a', 'regional_indicator_b', 'regional_indicator_c', 'regional_indicator_d', 'regional_indicator_e', 'regional_indicator_f', 'regional_indicator_g', 'regional_indicator_h', 'regional_indicator_i', 'regional_indicator_j', 'regional_indicator_k', 'regional_indicator_l', 'regional_indicator_m', 'regional_indicator_n', 'regional_indicator_o', 'regional_indicator_p', 'regional_indicator_q', 'regional_indicator_r', 'regional_indicator_s', 'regional_indicator_t', 'regional_indicator_u', 'regional_indicator_v', 'regional_indicator_w', 'regional_indicator_x', 'regional_indicator_y', 'regional_indicator_z']
ALPHAMOJIRED = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
NUMBERMOJI = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

def setup(bot):
    bot.add_cog(Polls(bot))

class Polls(commands.Cog):
    """Cog to interface polls with discord."""

    def __init__(self, bot):
        self.bot = bot
        self.polls = self.load_polls()  # dict(int, set(Poll))

    def load_polls(self) -> Dict[int, Set[Poll]]:
        try:
            with open('polls.unm', 'rb') as f:
                return pickle.load(f)
        except:
            print('No poll object to load')
            return dict()

    def cog_unload(self):
        reload(poll)
        with open('polls.unm', 'wb') as f:
            pickle.dump(self.polls, f)

    def add_poll(self, poll):
        channel = poll.channel_id
        if channel in self.polls and len(self.polls[channel]) >= 5:
            return False
        for _polls in self.polls.values():
            for _poll in _polls:
                if poll.title == _poll.title:
                    return False

        if channel not in self.polls:
            self.polls[channel] = set()
            self.polls[channel].add(poll)
        else:
            self.polls[channel].add(poll)
        return True

    async def send_poll(self, poll: Poll, ctx):
        await ctx.send('```' + str(poll) + '```')
        # await self.send_poll_embed(poll, ctx)

    def set_author_footer(self, embed, poll: Poll):
        poll_owner = self.bot.get_user(poll.owner_id)
        embed.set_footer(text=f'Started by {poll_owner.display_name}',
                         icon_url=poll_owner.avatar_url
                         )

    def set_entry_field(self, embed, num, entry):
        embed.add_field(name='Votes: {:n}'.format(float(entry[1])),
                value=f'{NUMBERMOJI[num]} {entry[0]}',
                inline=False)

    def make_active_poll_embed(self, poll, ctx):
        sorted_entries = sorted(poll.entries.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title=f'Poll: **{poll.title}**',
                            description=f'Voting is enabled! `u.voteon {poll.title}` to vote.',
                            color=0x5783ae)
        for i, entry in enumerate(sorted_entries):
            if i > len(NUMBERMOJI):
                embed.add_field(name='Runners up:',
                                value=', '.join(y for _,y in sorted_entries[len(NUMBERMOJI):]),
                                inline=False)
                break  # add ellipsis equivalent
            self.set_entry_field(embed, i+1, entry)
        self.set_author_footer(embed, poll)
        return embed

    def make_inactive_poll_embed(self, poll, ctx):
        sorted_entries = sorted(poll.entries.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title=f'Poll: **{poll.title}**',
                            description=f'Voting is **not** enabled. `u.begin {poll.title}` to open it up!',
                            color=0x5783ae)
        for i, entry in enumerate(sorted_entries):
            if i > len(NUMBERMOJI):
                break  # add ellipsis equivalent
            self.set_entry_field(embed, i+1, entry)
        self.set_author_footer(embed, poll)
        return embed

    def make_poll_embed(self, poll: Poll, ctx):
        # divide into multiple methods, probably
        if poll.active:
            return self.make_active_poll_embed(poll, ctx)
        else:
            return self.make_inactive_poll_embed(poll, ctx)

    async def send_poll_embed(self, poll: Poll, ctx):
        await ctx.send(embed=self.make_poll_embed(poll, ctx))

    @commands.command(aliases=['p'])
    async def poll(self, ctx, title: str):
        """Create a poll with a one-word title!"""
        poll = Poll(title, ctx.guild.id, ctx.channel.id, ctx.author.id)
        if not self.add_poll(poll):
            await ctx.send('Couldn\'t create poll')
            return
        # else:
        #     await ctx.send('Poll added')
        # await self.send_poll(poll, ctx)
        await ctx.send('Poll added! Send some entries to vote on:\n'+
                       'e.g. `entry one, entry two, etc`')

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        r = await self.bot.wait_for('message', check=check)
        entries = r.content.split(', ')
        poll.add_entries(entries)
        await ctx.send('Poll created!', embed=self.make_poll_embed(poll, ctx))

    def activate(self, poll):
        poll.active = True

    def deactivate(self, poll):
        poll.active = False
        del self.polls[poll]

    @commands.command(aliases=['beginpoll'])
    async def begin(self, ctx, title: str):
        """Turn on voting for a poll!"""
        for poll in self.polls[ctx.channel.id]:
            if poll.title == title:
                self.activate(poll)
                await ctx.send(f'Poll activated! `u.show {poll.title}` to see the results after voting!')
                await self.send_votable(ctx, poll)

    def get_poll(self, channel_id: int, title: str) -> Poll:
        for poll in self.polls[channel_id]:
            if poll.title == title:
                return poll
        raise KeyError("Poll not found")

    async def send_votable(self, ctx, poll: Union[str, Poll]):
        if type(poll) is str:
            poll = self.get_poll(ctx.channel.id, poll)
        i = 0
        reaction_calls = list()
        for title in poll.entries.keys():
            # msg = await ctx.send(':' + ALPHAMOJI[i] + ': ' + title)
            msg = await ctx.send('**' + title + '**')
            for j in range(1,4):
                reaction_calls.append(msg.add_reaction(NUMBERMOJI[j]))
            self.listen_to(msg, poll)
            i += 1
        await asyncio.gather(*reaction_calls)

    @commands.command(aliases=['vote'])
    async def voteon(self, ctx, title: str):
        """Send a poll to be voted on!"""
        poll = self.get_poll(ctx.channel.id, title)
        if not poll.active:
            await ctx.send(f'Voting on {poll.title} has not begun yet. If you wanna get \'er movin\','+
                           f'say `u.begin {poll.title}`.')
        await self.send_votable(ctx, title)

    def listen_to(self, msg: discord.Message, poll: Poll):
        poll.register_message(msg.id)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        msg = reaction.message
        channel = msg.channel
        if channel.id in self.polls.keys():
            for poll in self.polls[channel.id]:
                if msg.id in poll.active_messages:
                    poll.add_vote(self.entry_from(msg),
                                  self.voter_from(user),
                                  self.degree_from(reaction))
                    await asyncio.sleep(1)
                    await reaction.remove(user)

    def entry_from(self, msg: discord.Message) -> str:
        print(f'Getting entry title from {msg.content}')
        out = msg.content[2:-2]
        print(f'Got entry title {out}')
        return out

    def voter_from(self, user) -> Voter:
        return Voter(user.id, user.display_name)

    def degree_from(self, reaction: discord.Reaction) -> int:
        deg = NUMBERMOJI.index(reaction.emoji)
        print(f'Got degree {deg} from {str(reaction)}')
        return deg

    @commands.command(aliases=['showpoll', 'results'])
    async def show(self, ctx, title: str, *rest):
        """See the results of a poll!"""
        if rest == '-d':
            await self.send_poll(self.get_poll(ctx.channel.id, title), ctx)
        else:
            await self.send_poll_embed(self.get_poll(ctx.channel.id, title), ctx)

    @commands.command(name='list', aliases=['listpolls', 'showpolls'])
    async def _list(self, ctx):
        """See what polls are out there!"""
        out = ''
        if ctx.channel.id not in self.polls or len(self.polls[ctx.channel.id]) == 0:
            await ctx.send('There are no active polls right now. Make your own with `u.poll <title>`!')
        else:    
            for poll in self.polls[ctx.channel.id]:
                out += '\n**' + poll.title + '**'
            await ctx.send(out)

    @commands.command(aliases=['add','addentry'])
    async def addto(self, ctx, title: str, *, entries: str):
        """Add some entries to a poll!"""
        self.get_poll(ctx.channel.id, title).add_entries(entries.split(', '))
        await ctx.send('Added')

    @commands.command(aliases=[], hidden=True)
    async def combine(self, ctx, title: str, *, entries: str):
        """Combine entries and their votes into one entry."""
        # needs a usability and accuracy rework
        self.get_poll(ctx.channel.id, title).combine_entries(*entries.split(', '))

    @commands.is_owner()
    @commands.command(aliases=['reset'], hidden=True)
    async def resetpolls(self, ctx):
        self.polls: Dict[int, Set[Poll]] = dict()
