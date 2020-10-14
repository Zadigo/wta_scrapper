import csv
import os
from collections import Counter, OrderedDict
from functools import cached_property
from itertools import chain

from wta_scrapper.utils import BASE_DIR

SOURCE_PATH = os.path.join(BASE_DIR, 'sources')

class SourceFile:
    """
    Opens a source to run various operations on it

    Parameters

        filename (str): the source file to open
    """
    def __init__(self, filename):
        file_path = os.path.join(SOURCE_PATH, filename)
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = csv.reader(f)
            file_data = list(data).copy()
        
        self.file_data = file_data
        self.tournaments = self._populate

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__str__()})'

    def __str__(self):
        return str(self._populate)

    def __enter__(self):
        return self.file_data

    def __exit__(self, exc_type, exc_value, exc_traceback):
        return False

    def __getitem__(self, name):
        return self.tournaments[name]

    @staticmethod
    def _create_dict():
        tournaments = OrderedDict(
            {
                'Australian Open': [],
                'Roland Garros': [],
                'Wimbledon': [],
                'US Open': []
            }
        )
        return tournaments

    @cached_property
    def as_dict(self):
        tournaments = self._create_dict()

        names = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']
        
        for i, item in enumerate(self.file_data):
            if i != 0:
                for name in names:
                    tournaments[name].append(
                        {'year': item[0], 'name': item[1]}
                    )

        return tournaments

    @cached_property
    def every(self):
        """
        Return every player from the file regardless
        of how many times they appear

        Returns

            (chain): list of players
        """
        players = []
        keys = self.tournaments.keys()
        for key in keys:
            players.append(self.tournaments[key])
        return chain(*players)


    @cached_property
    def unique(self):
        """
        Return unique players from the file
        """
        return set(self.every)

    @cached_property
    def _populate(self):
        tournaments = self._create_dict()

        for i, item in enumerate(self.file_data):
            if i != 0:
                tournaments['Australian Open'].append(item[1])
                tournaments['Roland Garros'].append(item[2])
                tournaments['Wimbledon'].append(item[3])
                tournaments['US Open'].append(item[4])

        return tournaments

    def count(self, unique=False):
        if unique:
            return f'Found {len(list(self.unique))} unique players.'
        return f'Found {len(list(self.every))} players.'

    def count_by(self, tournament=None):
        """Count the amount of times each player
        appears in a specific column

        Parameter

            tournament (str): tournament name

        Returns

            (counter): a counter object
        """
        if tournament is not None:
            return Counter(self.tournaments.get(tournament, None))
        else:
            return Counter(self.every)
