from enum import Enum, auto
from math import ceil
from typing import Dict, List, Optional, Set, Tuple, Union

class PollEnums(Enum):
    SUCCESS = auto()
    VOTE_ALREADY_PRESENT = auto()
    MAX_VOTES_HIT = auto()
    POLL_NOT_ACTIVE = auto()


class Voter():
    def __init__(self, id: int, name: Optional[str]):
        self.id = id
        self.name = name

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self.name) + ':' + str(self.id)

    def __hash__(self):
        return self.id


class EntryVotes():
    """This class stores the votes for a single poll entry."""
    def __init__(self, votes: Optional[Dict[int, Set[Voter]]], ordinance=1):
        """Construct an EntryVotes object. If votes is none, construct an empty list."""
        if votes and type(votes) is not dict:
            raise RuntimeError("Votes parameter is not of type dict")
        elif not votes:
            votes = dict()
        for i in range(1, ordinance+1):
            if i not in votes.keys():
                votes[i] = set()
        self.votes: Dict[int, Set[Voter]] = votes
        self.ordinance = ordinance

    def add_vote(self, degree: int, voter: Voter):
        if voter in self.votes[degree]:
            return PollEnums.VOTE_ALREADY_PRESENT
        self.votes[degree].add(voter)
        return PollEnums.SUCCESS

    def remove_vote(self, degree: int, voter: Voter):
        self.votes[degree].remove(voter)

    def remove_votes(self):
        """Reinitialize the votes dict to reset votes."""
        self.votes = dict()
        for i in range(1, self.ordinance+1):
            self.votes[i] = set()

    def remove_votes_from(self, voter):
        """Remove votes from a specific voter."""
        for entry_votes in self.votes.values():
            if voter in entry_votes:
                print(f'Removing vote from user {voter}')
                entry_votes.remove(voter)

    def change_vote(self, old_deg: int, new_deg: int, voter: Voter):
        self.remove_vote(old_deg, voter)
        self.add_vote(new_deg, voter)

    def num_votes_by(self, voter: Voter, degree: int):
        total = 0
        if voter in self.votes[degree]:
            total += 1
        return total

    def set_ordinance(self, new: int):
        diff = self.ordinance - new
        if self.ordinance == new:
            return
        elif self.ordinance < new:
            # add new sets for votes
            for i in range(self.ordinance+1, new+1):
                self.votes[i] = set()
        else:  # self.ordinance > new
            for i in range(new+1, self.ordinance+1):
                del self.votes[i]
        self.ordinance = new

    def __str__(self) -> str:
        return str(self.votes)

    def __repr__(self):
        return self.__str__()

    def __float__(self) -> float:
        out = 0
        for i, v in enumerate(self.votes.values()):
            # if i == 0:
            #     continue  # first elem always zero
            out += len(v) / (2**(i))
        return out

    def __int__(self) -> int:
        return int(float(self))

    def __add__(self, other):
        out = dict()  # list(set(Voter))
        for c in range(1, max(len(self.votes), len(other.votes))):
            if c < len(self.votes) and c < len(other.votes):
                out[c] = self.votes[c].union(other.votes[c])
            elif c < len(self.votes):
                out[c] = self.votes[c]
            else:
                out[c] = other.votes[c]
        return EntryVotes(ordinance=self.ordinance, votes=out)

    def __lt__(self, other):
        return float(self) < float(other)

    def __contains__(self, item):
        if type(item) is int:
            item = Voter(item, None)
        else:
            raise TypeError('Containment test must be int or Voter')
        for s in self.votes.values():
            if item in s:
                return True
        return False

    def __eq__(self, other):
        if self.votes.keys() != other.votes.keys():
            return False
        else:
            for k in self.votes.keys():
                if self.votes[k] != other.votes[k]:
                    return False
        return True


class Poll():
    """A poll object!
    
    This class interfaces between external sources and EntryVotes objects.
    Thus, this class acts as a restrictor for what can and can't be done
    with EntryVotes objects. For example, this class enforces an ordinance of
    either 3 or 1 on EntryVotes objects, even though the datatype seems to support
    any value.
    """

    def __init__(self, title, guild_id, channel_id, owner_id,
                 active=False, num_votes=1, can_vote_for_half=True, ordinal=False,
                 protected=False, active_messages: Optional[set]=None,
                 entries: Optional[Dict[str, EntryVotes]]=None):
        self.title = title
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.owner_id = owner_id
        self.protected = protected
        self.active = active
        self.can_vote_for_half = can_vote_for_half
        self.num_votes_per_person = num_votes
        self.ordinal = ordinal
        self.entries: Dict[str, EntryVotes] = dict() if not entries else entries
        self.active_messages = set() if not active_messages else active_messages
        # init self.num_votes_per_person
        self.set_num_votes_per_person(num=num_votes, half=can_vote_for_half)

    def open_voting(self):
        self.active = True

    def close_voting(self):
        self.active = False

    def add_vote(self, entry: str, voter: Voter, degree: int) -> PollEnums:
        if not self.active:
            print(f'Poll {self.title} is not active.')
            return PollEnums.POLL_NOT_ACTIVE
        elif voter in self.entries[entry].votes[degree]:
            print('user has already voted for that entry and degree')
            return PollEnums.VOTE_ALREADY_PRESENT
        elif self.num_votes_by(voter, degree) >= self.num_votes_per_person:
            print(f'Voter {voter.name} already has the max number '+
                  f'of votes of degree {degree} on {self.title}')
            return PollEnums.MAX_VOTES_HIT
        return self.entries[entry].add_vote(degree, voter)

    def set_ordinal(self, ordinal: bool):
        self.ordinal = ordinal
        for title, entry in self.entries.items():
            entry.set_ordinance(3 if ordinal else 1)

    def set_num_votes_per_person(self, num: int =1, half: bool =False):
        if half:
            # half, rounded down, min of 1
            self.num_votes_per_person = max(len(self.entries) // 2, 1)
        else:
            self.num_votes_per_person = num
        print('set num votes to', self.num_votes_per_person)

    def update_num_votes(self):
        self.set_num_votes_per_person(num=self.num_votes_per_person,
                                      half=self.can_vote_for_half)

    def num_votes_by(self, voter: Union[int, Voter], degree):
        if type(voter) is int:
            voter = Voter(voter, None)
        total = 0
        for entry in self.entries:
            total += self.entries[entry].num_votes_by(voter, degree)
        return total

    def add_entry(self, entry):
        if entry not in self.entries.keys():
            self.entries[entry] = EntryVotes(None, ordinance=3 if self.ordinal else 1)
            self.update_num_votes()
        else:
            print(f'{entry} already in poll')

    def add_entries(self, _entries: List[str]):
        for entry in _entries:
            self.add_entry(entry)

    def combine_entries(self, a: str, b: str):
        """Combines the votes of two entries a and b into a."""
        if a not in self.entries or b not in self.entries:
            raise KeyError(f'{a if a not in self.entries else b} not in entries')
        self.entries[a] = self.entries[a] + self.entries[b]
        del self.entries[b]

    def combine_n_entries(self, *entries):
        # if any([e not in self.entries.keys() for e in entries]):
        #     raise KeyError(f'Not all entries are in the poll')  # bad UX
        base = None
        for e in entries:
            if e not in self.entries.keys():
                continue
            if not base:
                base = e
            else:
                self.entries[base] += self.entries[e]
                del self.entries[e]

    def remove_entry(self, entry: str):
        try:
            del self.entries[entry]
            self.update_num_votes()
        except:
            print(f'{entry} not in entries')

    def remove_votes_from_user(self, id: int):
        for entry in self.entries.values():
            entry.remove_votes_from(Voter(id, None))

    def remove_all_votes(self):
        for entry in self.entries.values():
            entry.remove_votes()

    def register_message(self, message: int):
        self.active_messages.add(message)

    def unregister_message(self, message: int):
        self.active_messages.remove(message)

    def unregister_messages(self):
        self.active_messages = set()

    def __str__(self):
        return 'Poll(title={0.title}, active={0.active}, ordinal={0.ordinal}, votes={0.entries})'\
               .format(self)

    def __eq__(self, other):
        print('\n\n',self.__dict__,'\n\n',other.__dict__,'\n')
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.__dict__.values())

    def __repr__(self):
        return self.__str__()
