import datetime
import unittest
from collections import OrderedDict
from unittest.main import main

from wta.app import MatchScrapper


def init_scrapper(build=False):
    instance = MatchScrapper(filename='test_page.html')
    if build:
        instance.build('player-matches__tournament')
    return instance


class TestEmptyScrap(unittest.TestCase):
    def setUp(self):
        self.scrapper = init_scrapper()

    def test_is_list(self):
        self.assertIsInstance(self.scrapper.tournaments, list)

    def test_deep_clean(self):
        s = '\n      Eugenie Bouchard'
        self.assertEqual(self.scrapper._deep_clean(s), ['Eugenie', 'Bouchard'])

    def test_date_parsing(self):
        d = '20-Oct 26, 2020'
        result = self.scrapper._parse_date(d)
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result.year, 2020)

    def test_normalizing(self):
        s = ' EUGENIE bouchard '
        self.assertEqual(self.scrapper._normalize(s), 'Eugenie Bouchard')
        self.assertEqual(self.scrapper._normalize(s, as_title=True), 'Eugenie Bouchard')


class Constructors(unittest.TestCase):
    def setUp(self):
        self.scrapper = init_scrapper()

    def test_parse_tournament_header(self):
        divs = self.scrapper.soup.find_all('div')
        for div in divs:
            if div.has_attr('class'):
                class_attrs = div.attrs['class']
                if 'player-matches__tournament' in class_attrs:
                    headers = div.find('div', 'player-matches__tournament-header')
        result = self.scrapper._parse_tournament_header(headers)
        self.assertIsInstance(result, OrderedDict)

    def test_construct_tournament_header(self):
        name, _ = self.scrapper._construct_tournament_header([])
        self.assertIsNone(name)

    def test_construct_tournament_header_2(self):
        name, values = self.scrapper._construct_tournament_header([1, [2, 'Paris, France'], 4, 5, 6])
        self.assertIsInstance(values, dict)
        self.assertEqual(name, 'Paris')
        self.assertEqual(values['country'], 'France')

if __name__ == "__main__":
    unittest.main()
