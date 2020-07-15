from poll import EntryVotes, Voter
import unittest

VOTER1 = Voter(-1, 'test1')
VOTER2 = Voter(-2, 'test2')


class EntryVotesUnordinalTest(unittest.TestCase):

    def setUp(self):
        self.e = EntryVotes()

    def test_ev_has_no_votes(self):
        for v in self.e.votes.values():
            self.assertEqual(len(v), 0)

    def test_new_ev_ordinance_is_one(self):
        self.assertEqual(self.e.ordinance, 1)

    def test_new_ev_ordinance_equals_votes_length(self):
        self.assertEqual(self.e.ordinance, len(self.e.votes))

    def test_after_add_vote_votes_are_not_empty(self):
        self.e.add_vote(1, VOTER1)
        for v in self.e.votes.values():
            self.assertNotEqual(len(v), 0)

    def test_after_add_vote_votes_length_is_one(self):
        self.e.add_vote(1, VOTER1)
        for v in self.e.votes.values():
            self.assertEqual(len(v), 1)

    def test_after_one_add_one_remove_has_no_votes(self):
        self.e.add_vote(1, VOTER1)
        self.e.remove_vote(1, VOTER1)
        self.test_ev_has_no_votes()

    def test_after_one_add_remove_votes_from_has_no_votes(self):
        self.e.add_vote(1, VOTER1)
        self.e.remove_votes_from(VOTER1)
        self.test_ev_has_no_votes()

    def test_after_one_add_remove_all_votes_has_no_votes(self):
        self.e.add_vote(1, VOTER1)
        self.e.remove_votes()
        self.test_ev_has_no_votes()

    def test_after_one_add_votes_by_voter_is_one(self):
        self.e.add_vote(1, VOTER1)
        self.assertEqual(self.e.num_votes_by(VOTER1, 1), 1)

    def test_after_two_voters_votes_by_voter1_is_one(self):
        self.e.add_vote(1, VOTER1)
        self.e.add_vote(1, VOTER2)
        self.assertEqual(self.e.num_votes_by(VOTER1, 1), 1)

    def test_after_two_voters_votes_by_voter2_is_one(self):
        self.e.add_vote(1, VOTER1)
        self.e.add_vote(1, VOTER2)
        self.assertEqual(self.e.num_votes_by(VOTER2, 1), 1)

    def test_two_new_ev_are_equal(self):
        self.assertEqual(self.e, EntryVotes())

    def test_two_ev_with_voter1_vote_are_equal(self):
        e2 = EntryVotes()
        self.e.add_vote(1, VOTER1)
        e2.add_vote(1, VOTER1)
        self.assertEqual(self.e, e2)

    def test_two_ev_one_has_voter1_vote_not_equal(self):
        e2 = EntryVotes()
        self.e.add_vote(1, VOTER1)
        self.assertNotEqual(self.e, e2)

    def test_value_of_one_vote_is_1(self):
        self.e.add_vote(1, VOTER1)
        self.assertEqual(int(self.e), 1)

    def test_value_of_emtpy_ev_is_0(self):
        self.assertEqual(int(self.e), 0)

    def test_value_of_two_votes_is_two(self):
        self.e.add_vote(1, VOTER1)
        self.e.add_vote(1, VOTER2)
        self.assertEqual(int(self.e), 2)

    def test_value_of_combined_ev_is_zero(self):
        self.assertEqual(int(self.e + EntryVotes()), 0)

    def test_after_one_add_each_value_of_combined_ev_is_1(self):
        self.e.add_vote(1,VOTER1)
        e2 = EntryVotes()
        e2.add_vote(1,VOTER1)
        self.assertEqual(int(self.e + EntryVotes()), 1)

    # def test_after_one_add_each_of_unique_voters_value_of_combined_ev_is_2(self):
    #     self.e.add_vote(1,VOTER1)
    #     e2 = EntryVotes()
    #     e2.add_vote(1,VOTER2)
    #     self.assertEqual(int(self.e + EntryVotes()), 2)


if __name__ == '__main__':
    unittest.main()
