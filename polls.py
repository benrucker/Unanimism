import asyncio
import discord
from discord.ext import commands, tasks
from importlib import reload
import os
import pickle
import poll
from poll import Poll, PollEnums, Voter
import random
from typing import Dict, List, Optional, Set, Union

ALPHAMOJI = ['regional_indicator_a', 'regional_indicator_b', 'regional_indicator_c', 'regional_indicator_d', 'regional_indicator_e', 'regional_indicator_f', 'regional_indicator_g', 'regional_indicator_h', 'regional_indicator_i', 'regional_indicator_j', 'regional_indicator_k', 'regional_indicator_l', 'regional_indicator_m', 'regional_indicator_n', 'regional_indicator_o', 'regional_indicator_p', 'regional_indicator_q', 'regional_indicator_r', 'regional_indicator_s', 'regional_indicator_t', 'regional_indicator_u', 'regional_indicator_v', 'regional_indicator_w', 'regional_indicator_x', 'regional_indicator_y', 'regional_indicator_z']
ALPHAMOJIRED = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
NUMBERMOJI = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
YES = ['yes','yeah','yep','yeppers','of course','ye','y','ya','yah', 'yea', 'yush']
NO  = ['no','n','nope','nay','nada', 'nah', 'na']


def setup(bot):
    print('Loading Polls Extension')
    bot.add_cog(Polls(bot, 'polls.unm', True))


class Polls(commands.Cog):
    """Cog to interface polls with discord."""

    def __init__(self, bot, polls_file, enable: bool):
        self.bot = bot
        self.polls = self.load_polls(polls_file)  # dict(int, set(Poll))
        if enable:
            self.task_save_polls.start()

    def load_polls(self, polls_file: str) -> Dict[int, Set[Poll]]:
        try:
            with open(polls_file, 'rb') as f:
                return pickle.load(f)
        except:
            print('No poll object to load')
            return dict()

    def save_polls(self, filename):
        print('saving polls')
        with open(filename, 'wb') as f:
            pickle.dump(self.polls, f)
            print(f'saved polls to {filename}')

    def cog_unload(self):
        # cleanup cannot go here due to it being a coroutine
        self.task_save_polls.cancel()
        self.save_polls('polls.unm')
        reload(poll)

    async def cleanup(self):
        # await self.remove_poll_reactions()
        await self.remove_votable_polls()

    async def remove_poll_reactions(self):
        for chanid, _polls in self.polls.items():
            chan = await self.bot.fetch_channel(chanid)
            for _p in _polls:
                for msg in _p.active_messages:
                    try:
                        m = await chan.fetch_message(msg)
                    except:
                        continue
                    print('removing reactions from', m.content)
                    await m.clear_reactions()
                _p.unregister_messages()

    async def remove_votable_polls(self):
        for chanid, _polls in self.polls.items():
            chan = await self.bot.fetch_channel(chanid)
            for _p in _polls:
                def check(message):
                    return message.id in _p.active_messages
                await chan.purge(check=check)
                _p.unregister_messages()

    def add_poll(self, poll):
        channel = poll.channel_id
        if channel in self.polls and len(self.polls[channel]) >= 5:
            print('channel limit hit')
            return False
        for _polls in self.polls.values():
            for _poll in _polls:
                if poll.title == _poll.title:
                    print('poll with that name already exists')
                    return False

        if channel not in self.polls:
            self.polls[channel] = set()
            self.polls[channel].add(poll)
        else:
            self.polls[channel].add(poll)
        return True

    async def send_poll(self, poll: Poll, ctx):
        await ctx.send('```' + str(poll) + '```')

    def set_author_footer(self, embed, poll: Poll):
        poll_owner = self.bot.get_user(poll.owner_id)
        embed.set_footer(text=f'Poll started by {poll_owner.display_name}',
                         icon_url=poll_owner.avatar_url
                         )

    def set_entry_field(self, embed, num, entry):
        embed.add_field(name='Votes: {:n}'.format(float(entry[1])),
                        value=f'{NUMBERMOJI[num]} {entry[0]}',
                        inline=False)

    def active_embed_args(self, poll):
        return dict(title=f'Poll: **{poll.title}**',
                    description=f'Voting is enabled! `u.voteon {poll.title}` to vote, or `u.addto {poll.title}` to add entries!',
                    color=0x5783ae
                    )

    def inactive_embed_args(self, poll):
        return dict(title=f'Poll: **{poll.title}**',
                    description=f'Voting is **not** enabled. `u.begin {poll.title}` to open it up, or `u.addto {poll.title}` to add entries!',
                    color=0x5783ae
                    )

    def make_active_poll_embed(self, poll, ctx):
        sorted_entries = sorted(poll.entries.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(**self.active_embed_args(poll))
        for i, entry in enumerate(sorted_entries):
            if i > len(NUMBERMOJI):
                embed.add_field(name='Runners up:',
                                value=', '.join(y for _,y in sorted_entries[len(NUMBERMOJI):]),
                                inline=False)
                break
            self.set_entry_field(embed, i+1, entry)
        self.set_author_footer(embed, poll)
        return embed

    def make_inactive_poll_embed(self, poll, ctx):
        sorted_entries = sorted(poll.entries.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(**self.inactive_embed_args(poll))
        for i, entry in enumerate(sorted_entries):
            if i > len(NUMBERMOJI):
                break  # add ellipsis equivalent
            self.set_entry_field(embed, i+1, entry)
        self.set_author_footer(embed, poll)
        return embed

    def make_unordered_poll_embed(self, poll, ctx):
        embed = discord.Embed(**(self.active_embed_args(poll) if poll.active else self.inactive_embed_args(poll)))
        embed.add_field(name='Entries:',
                        value=':small_blue_diamond: ' + '\n:small_blue_diamond: '.join(poll.entries.keys()),
                        inline=False)
        self.set_author_footer(embed, poll)
        return embed

    def make_poll_embed(self, poll: Poll, ctx):
        # divide into multiple methods, probably
        if poll.active:
            return self.make_active_poll_embed(poll, ctx)
        else:
            return self.make_inactive_poll_embed(poll, ctx)

    async def send_poll_results_embed(self, poll: Poll, ctx):
        await ctx.send(embed=self.make_poll_embed(poll, ctx))

    async def send_unordered_poll_embed(self, poll: Poll, ctx):
        await ctx.send(embed=self.make_unordered_poll_embed(poll, ctx))

    async def get_entries_from_user(self, ctx, text: str = 'Poll added! Send some entries to be voted on:') -> List[str]:
        await ctx.send(text + '\ne.g. `entry one, entry two, etc`')

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        r = await self.bot.wait_for('message', check=check)
        entries: list = r.content.split(', ')
        return entries
        # poll.add_entries(entries)

    async def get_config_from_user(self, ctx, poll: Poll, new_poll=False):
        # protected, number of choices per vote, max votes per poll
        await ctx.send(
            f'Thanks for making a poll! Do you want this poll to be private? **({random.choice(YES)}/{random.choice(NO)})**\n' +
            'This means **only you** can see the results, but everyone can still vote.'
        )

        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel == ctx.channel
        r = await self.bot.wait_for('message', check=check)
        while True:
            if r.content.lower() in YES:
                poll.protected = True
                break
            elif r.content.lower() in NO:
                poll.protected = False
                break
            else:
                await ctx.send(f'I didn\'t quite catch that. Respond with **{random.choice(YES)}** or **{random.choice(NO)}**.')
                r = await self.bot.wait_for('message', check=check)
        print(f'set poll {poll.title} to protected={poll.protected}')

    @commands.command(aliases=['p'])
    async def poll(self, ctx, title: str):
        """Create a poll with a one-word title!"""
        # add check for poll with existing name
        poll = Poll(title, ctx.guild.id, ctx.channel.id, ctx.author.id)
        await self.get_config_from_user(ctx, poll, new_poll=True)
        entries = await self.get_entries_from_user(ctx)
        poll.add_entries(entries[:poll.max_entries])  # TODO add feedback for max entries
        if not self.add_poll(poll):
            await ctx.send('Couldn\'t create poll')
            return
        await ctx.send('Poll created!', embed=self.make_poll_embed(poll, ctx))

    def activate(self, poll):
        poll.active = True

    def deactivate(self, poll):
        poll.active = False
        # del self.polls[poll]

    @commands.command(aliases=[])
    async def begin(self, ctx, title: str):
        """Turn on voting for a poll!"""
        for poll in self.polls[ctx.channel.id]:
            if poll.title == title:
                self.activate(poll)
                await ctx.send(f'Poll activated! `u.results {poll.title}` to see the results after voting!')
                await self.send_votable(ctx, poll)

    @commands.command(aliases=[])
    async def end(self, ctx, title: str):
        """End voting on a poll."""
        _p = self.get_poll(ctx.channel.id, title)
        if _p.protected and ctx.author.id != _p.owner_id:
            await ctx.send('Sorry mate, this poll can only be closed by the owner!')
        else:
            self.deactivate(_p)
            await ctx.send('Poll has been deactivated!')

    def delete_poll(self, poll: Poll):
        """Deletes a poll. Does not check membership."""
        self.polls[poll.channel_id].remove(poll)

    @commands.command(aliases=[])
    async def removepollforever(self, ctx, title: str):
        """Remove a poll from the channel. Warning: permanent!"""
        _p = self.get_poll(ctx.channel.id, title)
        if _p.owner_id == ctx.author.id:
            self.delete_poll(_p)
            await ctx.send(f'The {_p.title} poll is gone. Forever!')

    def get_poll(self, channel_id: int, title: str) -> Poll:
        for poll in self.polls[channel_id]:
            if poll.title.lower() == title.lower():
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
            await asyncio.sleep(.3)
            if poll.ordinal:
                for j in range(1,4):
                    reaction_calls.append(msg.add_reaction(NUMBERMOJI[j]))
            else:
                reaction_calls.append(msg.add_reaction('☑️'))
            self.listen_to(msg, poll)
            i += 1
        async with ctx.typing():
            await asyncio.gather(*reaction_calls)
            await ctx.send(f'Click the reactions to cast a vote! You can vote up to {poll.num_votes_per_person} times on this poll.')

    @commands.command(aliases=['vote'])
    async def voteon(self, ctx, title: str):
        """Sends a poll to be voted on!"""
        poll = self.get_poll(ctx.channel.id, title)
        if not poll.active:
            await ctx.send(f'Voting on {poll.title} has not begun yet. If you wanna get \'er movin\', ' +
                           f'say `u.begin {poll.title}`.')
        else:
            await self.send_votable(ctx, title)

    def listen_to(self, msg: discord.Message, poll: Poll):
        poll.register_message(msg.id)

    async def respond_to_vote(self, return_code: PollEnums, user, poll: Poll, entry: str, degree: int):
        if return_code == PollEnums.SUCCESS:
            out = f'Your vote for **{entry}** has been counted! '
            remaining = poll.num_votes_per_person - poll.num_votes_by(user.id, degree)
            out += f'You have {remaining} vote{"" if remaining == 1 else "s"} remaining!'
            await user.send(out)
        elif return_code == PollEnums.VOTE_ALREADY_PRESENT:
            await user.send(f'Error: You\'ve already voted for **{degree}-{entry}**. ' +
                            f'Say `u.myvotes {poll.title}` in the channel to see what you voted for!')
        elif return_code == PollEnums.MAX_VOTES_HIT:
            await user.send(f'You\'ve hit the max number of votes on the poll **{poll.title}**. ' +
                            f'Say `u.myvotes {poll.title}` in the channel to see what you voted for or ' +
                            f'`u.resetmyvotes {poll.title}` to reset your votes so you can vote again.')
        elif return_code == PollEnums.POLL_NOT_ACTIVE:
            await user.send(f'Error: the poll **{poll.title}** is not accepting votes right now. ' +
                            f'Send `u.activate {poll.title}` in the channel to reopen voting.')

    async def process_vote(self, reaction, user, poll):
        msg = reaction.message
        channel = msg.channel # noqa
        entry = self.entry_from(msg)
        voter = self.voter_from(user)
        degree = self.degree_from(reaction)
        result = poll.add_vote(entry,
                               voter,
                               degree)
        await self.respond_to_vote(result, user, poll, entry, degree)
        await asyncio.sleep(1)
        await reaction.remove(user)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        msg = reaction.message
        channel = msg.channel
        if channel.id in self.polls.keys():
            for poll in self.polls[channel.id]:
                if msg.id in poll.active_messages:
                    await self.process_vote(reaction, user, poll)

    def entry_from(self, msg: discord.Message) -> str:
        print(f'Getting entry title from {msg.content}')
        out = msg.content[2:-2]
        print(f'Got entry title {out}')
        return out

    def voter_from(self, user) -> Voter:
        return Voter(user.id, user.display_name)

    def degree_from(self, reaction: discord.Reaction) -> int:
        if reaction.emoji in NUMBERMOJI:
            deg = NUMBERMOJI.index(reaction.emoji)
        elif reaction.emoji == '☑️':
            deg = 1
        else: raise KeyError('Invalid voting emoji')
        print(f'Got degree {deg} from {str(reaction)}')
        return deg

    @commands.command(aliases=[])
    async def results(self, ctx, title, here: Optional[str]):
        """See the results of a poll!"""
        _p = self.get_poll(ctx.channel.id, title)
        if _p.protected:
            if ctx.author.id == _p.owner_id:
                if here and here.lower() == 'here':
                    dest = ctx
                else:
                    dest = ctx.author
            else:
                await ctx.send('This poll is protected, so only the owner can see the results!')
                return
        else:
            dest = ctx
        await self.send_poll_results_embed(_p, dest)

    @commands.command(aliases=[])
    async def show(self, ctx, title: str):
        """See the contents of a poll!"""
        _p = self.get_poll(ctx.channel.id, title)
        await self.send_unordered_poll_embed(_p, ctx)

    @commands.command(name='list', aliases=[])
    async def _list(self, ctx):
        """See what polls are out there!"""
        out = ''
        if ctx.channel.id not in self.polls or len(self.polls[ctx.channel.id]) == 0:
            await ctx.send('There are no active polls right now. Make your own with `u.poll <title>`!')
        else:    
            for poll in self.polls[ctx.channel.id]:
                out += '\n**' + poll.title + '**'
            await ctx.send(out)

    @commands.command(aliases=[])
    async def addto(self, ctx, title: str, *, entries: Optional[str]):
        """Add some entries to a poll!"""
        _poll = self.get_poll(ctx.channel.id, title)
        if entries:
            _entries = entries.split(', ')
        else:
            _entries = await self.get_entries_from_user(ctx)
        cutoff = _poll.max_entries - len(_poll.entries)
        if cutoff == 0:
            out = f'**{_poll.title}** already has the max number of entries!'
        else:
            _entries = _entries[:cutoff]
            _poll.add_entries(_entries)
            out = f'Entries added! `u.show {_poll.title}` to see them!'
        if cutoff > 0:
            out += f' ({cutoff} entries were not added due to hitting the max of {_poll.max_entries})'
        await ctx.send(out)

    @commands.command(aliases=[], hidden=True)
    async def combine(self, ctx, title: str):
        """Combine entries and their votes into one entry."""
        poll = self.get_poll(ctx.channel.id, title)
        entries = await self.get_entries_from_user(ctx, text='Alright! Send the entries you want to combine:')
        poll.combine_n_entries(*entries)
        if len(entries) == 2:
            await ctx.send(f'**{entries[1]}** was combined with **{entries[0]}**.')
        else:
            await ctx.send(f'**{", ".join(entries[1:])}** were combined with **{entries[0]}**')

    @commands.command(aliases=[], hidden=True)
    async def removeentry(self, ctx, title: str):
        """Remove an entry from a poll."""
        poll = self.get_poll(ctx.channel.id, title)
        entries: List[str] = await self.get_entries_from_user(ctx, text='Alright! Send the entries you want to remove:')
        for entry in entries:
            poll.remove_entry(entry)
        await self.send_unordered_poll_embed(poll, ctx)

    @commands.command()
    async def edit(self, ctx, poll: str, *, options: str):
        """Edit your poll.

        Example usage: `u.edit <title> ordinal=False max_votes=1 protected=False`.
        
        Values:
        ordinal=true|false
        max_votes=<int>|half
        protected=true|false
        max_entries=<int>
        """
        p = self.get_poll(ctx.channel.id, poll)
        if ctx.author.id not in (p.owner_id, 173978157349601283):
            await ctx.send('Only the owner of a poll can edit its properties.')
            return
        out = ''
        pairs = [x.split('=') for x in options.split(' ')]
        for pair in pairs:
            if pair[0] == 'ordinal':
                v = pair[1].lower() == 'true'
                p.set_ordinal(v)
                out += f'set ordinal to {v}\n'
            if pair[0] == 'max_votes':
                try:
                    v = int(pair[1])
                    p.set_num_votes_per_person(num=v)
                except:
                    v = str(pair[1])
                    if v != 'half':
                        break
                    p.set_num_votes_per_person(half=True)
                finally:
                    out += f'set num votes to {v}\n'
            if pair[0] == 'protected':
                v = bool(pair[1])
                p.protected = v
                out += f'set protected to {v}\n'
            if pair[0] == 'max_entries':
                v = int(pair[1])
                p.max_entries = v
                out += f'set max entries to {v}\n'
        if out == '':
            out = 'No changes made'
        else:
            out = 'Changes:\n' + out
        await ctx.send(out)

    @commands.command(aliases=['rv'])
    async def resetmyvotes(self, ctx, poll: str):
        """Remove your votes from an open poll."""
        self.get_poll(ctx.channel.id, poll).remove_votes_from_user(ctx.author.id)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def resetallvotesfor(self, ctx, poll: str):
        p = self.get_poll(ctx.channel.id, poll)
        p.remove_all_votes()
        await ctx.send(f'Votes for **{p.title}** have been reset.')

    @commands.command(aliases=[])
    async def myvotes(self, ctx, poll: str):
        """Take a look at what you've voted for so far on a poll."""
        p = self.get_poll(ctx.channel.id, poll)
        v = Voter(ctx.author.id, None)  # membership tests don't require name
        out = f'__Your votes on **{p.title}**:__\n'
        for entry, entryvotes in p.entries.items():
            for pos in entryvotes.votes.keys():
                if v in entryvotes.votes[pos]:
                    out += f'{str(pos)+". " if p.ordinal else ""}{entry}\n'
        remaining = p.num_votes_per_person - p.num_votes_by(v, 1)
        out += f'You have {remaining} vote{"" if remaining == 1 else "s"} remaining! '
        out += f'Send `u.resetmyvotes {p.title}` back in the other channel to reset your votes!'
        await ctx.author.send(out)

    @commands.command()
    async def allvotes(self, ctx, poll: str):
        """WIP: see who voted for what on a poll. Warning: bad"""
        p = self.get_poll(ctx.channel.id, poll)
        if p.protected and ctx.author.id not in [p.owner_id, self.bot.owner_id]:
            await ctx.send('This poll is private, so only the owner can see the results!')
            return
        out = ''
        out2 = None
        for entry in p.entries.items():
            out += str(entry) + '\n'
        if len(out) > 2000:
            out2 = out[2000:]
            out = out[:2000]
        await ctx.author.send(out)
        if out2:
            await ctx.author.send(out2)

    @commands.is_owner()
    @commands.command(aliases=[], hidden=True)
    async def clearchannel(self, ctx):
        print(self.polls[ctx.channel.id])
        self.polls[ctx.channel.id] = set()
        print(self.polls[ctx.channel.id])
        await ctx.send('All the polls are gone. ')

    @commands.is_owner()
    @commands.command(aliases=[], hidden=True)
    async def resetpolls(self, ctx):
        self.polls: Dict[int, Set[Poll]] = dict()

    @commands.is_owner()
    @commands.command(aliases=['die'])
    async def しね(self, ctx):
        """Frame 1 OHKO"""
        await self.cleanup()
        self.bot.unload_extension('polls')
        await self.bot.close()

    def verify_saved_polls(self, filename):
        print('verifying save matches current state at', filename)
        dummy_polls = Polls(None, filename, False)
        # print(dummy_polls)
        # print(self)
        if self != dummy_polls:  # TODO will always fail rn
            print('saved poll does not match current state')
            return False
        print('saved poll matches current state')
        return True

    def finalize_saved_polls(self, filename):
        print('removing polls.unm')
        os.remove('polls.unm')
        print('renaming', filename, 'to polls.unm')
        os.rename(filename, 'polls.unm')
        print('renamed')

    @tasks.loop(hours=2)
    async def task_save_polls(self):
        # pause event loop
        print('backing up polls')
        backup = 'backup.unm'
        self.save_polls(backup)
        print('saved')
        if not self.verify_saved_polls(backup):
            print('backup does not match current state. aborting')
            return False
        print('finalizing backup')
        self.finalize_saved_polls(backup)
        # resume event loop

    @task_save_polls.before_loop
    async def task_before_save_polls(self):
        await self.bot.wait_until_ready()

    def __str__(self):
        out = ''
        for id in self.polls.keys():
            out += f'{id}:\n'
            for poll in self.polls[id]:
                out += f'\t{poll}\n'
        return out

    def __repr__(self):
        return self.__str__()
