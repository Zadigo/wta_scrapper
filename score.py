import json
import re

import numpy


class Score:
    """
    Format the score in order for it to be compatible
    with numpy

    Parameters
    ----------

        score (str): the tennis score as a string
        match state (bool, optional): the match result W or L. Defaults to None
    """

    def __init__(self, score: str, match_state=None):
        self.has_tie_breaks = False
        self.score_is_valid = False
        self.tie_breaks = 0

        mappings = []
        matched_regex = []

        # n - normal set
        # t - tie break
        regexes = [
            ('other', r'^(Bye|Retired|Walkover)'),
            # 5-1 Retired / 6-1 5-1 Retired
            ('n-r', r'^(\d\-\d)+\s?(Retired)$'),
            # Catch all other sets
            ('n-n', r'^(\d\-\d)(?:\(\d?\))?\s?(\d\-\d)(?:\(\d?\))?\s?(\d\-\d)?(?:\(\d?\))?$')
        ]

        score_as_list = []
        for mapping, regex in regexes:
            is_match = re.match(regex, score)
            if is_match:
                mappings.append(mapping)
                matched_regex.append(is_match)
                score_as_list = list(is_match.groups())

        # If multiple matches occur, the least accurate one
        # is used by default and it contains a None value which
        # should be filtered out
        score = list(filter(lambda x: x is not None, score_as_list))

        self.matched_regex = matched_regex

        self.literal_score = score_as_list
        self.match_state = match_state
        self.score = self._get_values(self.literal_score)

        for item in self.score:
            if (numpy.array_equal([7, 6], item) |
                    numpy.array_equal([6, 7], item)):
                self.has_tie_break = True
                self.tie_breaks += 1

    def __repr__(self):
        return f'{self.__class__.__name__}({self.score})'

    def __str__(self):
        return self.score_as_string

    @property
    def has_won_first_set(self):
        return True if not self.has_lost_first_set else False

    @property
    def has_lost_first_set(self):
        try:
            return (
                (self.score[0, 1] == 6) |
                (self.score[0, 1] == 7)
            )
        except:
            return False

    @property
    def is_valid(self):
        """
        Determines whether the score was matched
        correctly by the algorithm and that its
        values were parsed correctly
        """
        return self.score_is_valid

    def _get_values(self, score):
        """
        Parses the score and returns a numpy array
        of each score value

        Parameters
        ----------

            score (str): score a string
        """
        individual_numbers = []
        try:
            for value in score:
                if value is not None:
                    lhs, rhs = value.split('-')
                    individual_numbers.append([lhs, rhs])
        except:
            self.score_is_valid = False
            return []
        else:
            self.score_is_valid = True
            return numpy.array(individual_numbers, dtype='int32')

    @property
    def number_of_tie_breaks(self):
        return self.tie_breaks

    @property
    def number_of_sets(self):
        try:
            return list(self.score.shape)[0]
        except:
            return None

    @property
    def number_of_sets_literal(self):
        sets = self.number_of_sets

        if sets == 1:
            return 'one'

        if sets == 2:
            return 'two'

        if sets == 3:
            return 'three'

        return None

    @property
    def double_bagel(self):
        return numpy.array_equal([[0, 6], [0, 6]], self.score)

    @property
    def has_won_one_game(self):
        return (
            numpy.array_equal(numpy.array([[1, 6], [0, 6]]), self.score) |
            numpy.array_equal(numpy.array([[0, 6], [1, 6]]), self.score)
        )

    @property
    def score_as_string(self):
        str_scores = []
        scores = numpy.array(self.score.copy(), dtype='str')
        for values in scores:
            score = '-'.join(values)
            str_scores.append(score)
        return ' '.join(str_scores)

    @property
    def games_won(self):
        number_of_sets = self.score.shape[0]
        games_won = 0
        for i in range(number_of_sets):
            value = self.score[i, 0]
            if value == 6 or value == 7:
                value = self.score[i, 1]
            games_won += value
        return games_won

    @property
    def total_games(self):
        try:
            return self.score.sum()
        except:
            return 0

    def copy(self):
        klass = self.__class__(self.literal_score)
        return klass


def expand_scores(items, filename=None, update_file=False):
    """
    From a JSON file, implement additional information
    about a tennis score

    Args

        items (list): list of tournaments or matches
        filename (str, optional):
        update_file (bool, optional): Defaults to True
    """
    characteristics = items.pop(-1)
    for item in items:
        for values in item.values():
            for match in values['matches']:
                score = Score(match['details']['score'])

                match['details']['first_set'] = score.has_won_first_set
                match['details']['sets_literal'] = score.number_of_sets_literal
                match['details']['total_games'] = int(score.total_games)
                match['details']['has_tie_break'] = score.has_tie_breaks
                match['details']['tie_breaks'] = score.tie_breaks

    items.append(characteristics)
    if filename and update_file:
        with open(filename, 'w') as f:
            json.dumps(items, indent=4)
    return items
