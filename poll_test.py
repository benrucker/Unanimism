from poll import Poll
import unittest


class PollTest(unittest.TestCase):

    def setUp(self):
        self.p = Poll(title='testing', guild_id=-1, channel_id=-1, owner_id=-1)

    def test_new_poll_has_no_entries(self):
        self.assertEqual(len(self.p.entries), 0)

    def test_after_one_add_has_one_entry(self):
        self.p.add_entry('test1')
        self.assertEqual(len(self.p.entries), 1)

    def test_after_two_add_has_two_entries(self):
        self.p.add_entry('test1')
        self.p.add_entry('test2')
        self.assertEqual(len(self.p.entries), 2)

    def test_after_one_add_one_remove_entry_has_no_entries(self):
        self.p.add_entry('test1')
        self.p.remove_entry('test1')
        self.assertEqual(len(self.p.entries), 0)


# class PollVotingTest(unittest.TestCase):

#     def setUp(self):
#         self.p = Poll(title='testing', guild_id=-1, channel_id=-1, owner_id=-1)
#         self.p.add_entry('test')

#     def test_add_vote_


if __name__ == '__main__':
    unittest.main()
