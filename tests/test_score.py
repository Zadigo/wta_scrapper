import unittest
from wta_scrapper.app import Score

class TwoSetsLost(unittest.TestCase):
    def setUp(self):
        self.score = Score('1-62-6')

    def test_has_matched_regex(self):
        self.assertTrue(len(self.score.matched_regex) > 0)

    def test_literral_score(self):
        self.assertTrue(len(self.score.literal_score) > 0)

    def test_two_set_score(self):
        self.assertEqual(self.score.score_as_string, '1-6 2-6')

    def test_checks(self):
        self.assertEqual(self.score.has_lost_first_set, True)
        self.assertEqual(self.score.has_won_no_games, False)
        self.assertEqual(self.score.has_won_one_game, False)
        self.assertEqual(self.score.number_of_games, 15)
        self.assertEqual(self.score.number_of_sets, 2)
        self.assertEqual(self.score.is_valid, True)
        self.assertEqual(self.score.games_won, 3)


class TwoSetsWin(unittest.TestCase):
    def setUp(self):
        self.score = Score('6-06-3')

    def test_has_matched_regex(self):
        self.assertTrue(len(self.score.matched_regex) > 0)

    def test_literral_score(self):
        self.assertTrue(len(self.score.literal_score) > 0)

    def test_two_set_score(self):
        self.assertEqual(self.score.score_as_string, '6-0 6-3')

    def test_checks(self):
        self.assertEqual(self.score.has_lost_first_set, False)
        self.assertEqual(self.score.has_won_no_games, False)
        self.assertEqual(self.score.has_won_one_game, False)
        self.assertEqual(self.score.number_of_games, 15)
        self.assertEqual(self.score.number_of_sets, 2)
        self.assertEqual(self.score.is_valid, True)
        self.assertEqual(self.score.games_won, 3)


class ThreeSetsWin(unittest.TestCase):
    def setUp(self):
        self.score = Score('6-03-67-5')

    def test_has_matched_regex(self):
        self.assertTrue(len(self.score.matched_regex) > 0)

    def test_literral_score(self):
        self.assertTrue(len(self.score.literal_score) > 0)

    def test_two_set_score(self):
        self.assertEqual(self.score.score_as_string, '6-0 3-6 7-5')

    def test_checks(self):
        self.assertEqual(self.score.has_lost_first_set, False)
        self.assertEqual(self.score.has_won_no_games, False)
        self.assertEqual(self.score.has_won_one_game, False)
        self.assertEqual(self.score.number_of_games, 27)
        self.assertEqual(self.score.number_of_sets, 3)
        self.assertEqual(self.score.is_valid, True)
        self.assertEqual(self.score.number_of_sets_literal, 'three')
        self.assertEqual(self.score.games_won, 8)


class RetiredScore(unittest.TestCase):
    def setUp(self):
        self.score = Score('6-25-2 Retired')

    def test_has_matched_regex(self):
        self.assertTrue(len(self.score.matched_regex) > 0)

    def test_literral_score(self):
        self.assertTrue(len(self.score.literal_score) > 0)

    def test_two_set_score(self):
        self.assertEqual(self.score.score_as_string, '6-2 5-2')

    def test_checks(self):
        self.assertEqual(self.score.has_lost_first_set, False)
        self.assertEqual(self.score.has_won_no_games, False)
        self.assertEqual(self.score.has_won_one_game, False)
        self.assertEqual(self.score.number_of_games, 15)
        self.assertEqual(self.score.number_of_sets, 2)
        self.assertEqual(self.score.is_valid, True)
        self.assertEqual(self.score.number_of_sets_literal, 'two')
        self.assertEqual(self.score.games_won, 7)



if __name__ == "__main__":
    unittest.main()
