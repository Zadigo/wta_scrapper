import argparse
import csv
import datetime
import json
import logging
import os
import secrets
from collections import OrderedDict, defaultdict, deque
from functools import lru_cache

from bs4 import BeautifulSoup

from wta_scrapper.mixins import Mixins
from wta_scrapper.models import Query
from wta_scrapper.score import Score
from wta_scrapper.utils import BASE_DIR, autodiscover


def init_logger(name):
    logger = logging.Logger(name)

    format_str = '%(asctime)s :: %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


class MatchScrapper(Mixins):
    def __init__(self, filename=None):
        self.explorer = autodiscover()

        self.logger = init_logger(self.__class__.__name__)

        if filename is not None:
            with open(self.explorer(filename=filename), 'r') as _file:
                soup = BeautifulSoup(_file, 'html.parser')

            self.soup = soup
        self.tournaments = []

    def __enter__(self):
        return self.tournaments

    def __exit__(self, type, value, traceback):
        return False

    def __getitem__(self, index):
        return self.tournaments[0][index]

    def __eq__(self, value):
        keys = list(self.tournaments.keys())
        return value in keys

    def build(self, f, player_name=None, 
              year=None, date_as_string=True, 
              map_to_keys: dict = {}, **kwargs):
        """
        Main entrypoint for creating a new matches JSON file

        The application gets all the divs of the page and then filters
        them base on the provided criteria

        Parameters
        ----------

        - `f` criteria to use for filtering the divs that contains the data to parse
        
        - `player_name` name of the player to appear in the final returned value
        
        - `year` you can provide an explicity year to use for the returned values
            
        - `date_as_string` indicates whether the final date should be a string

        - `include_month` indicates if the month should be included in the final values

        - `date_of_birth` provide a date of birth if you wish to integrate calculations related
        to the player's date of birth and the dates related to the tournaments

        - `map_to_keys` if you want to swap the retrieved tournament name by one that is more
        suitable for the final return values use this parameter e.g. { Rogers cup by me: Rogers Cup }

        - `kwargs` any other values that you wish would appear in the final values 

        Notes
        -----
        
        This was built on the latest page structure of the WTA website which could also
        change in the future.

        """
        divs = self.soup.find_all('div')

        self.logger.info('Started.')

        content = self._filter(divs, f)
        if content:
            base = None
            for element in content:
                header = element.find_next('div')
                if header is not None:
                    if not header.is_empty_element:
                        attrs = header.get_attribute_list('class')[0]
                        if 'header' in attrs:
                            base = self._parse_tournament_header(header)

                    if base is not None:
                        # Construct the matches
                        table = element.find('table')
                        if not table.is_empty_element and table is not None:
                            updated_tournament = self._parse_matches(
                                table.find('tbody').find_all('tr'),
                                using=base
                            )
                        else:
                            updated_tournament = base

                        # Finally, integrate the footer
                        divs = header.parent.select('div')
                        footer = self._filter(divs, 'footer')
                        if footer:
                            updated_tournament = self._parse_footer(footer[-1], using=updated_tournament)

                        self.tournaments.append(updated_tournament)
                        # IMPORTANT: Reset the base in order to
                        # prevent the app from appending content
                        # to self.tournaments on each iteration
                        base = None


            self._finalize(
                player_name=player_name, 
                year=year, 
                date_as_string=date_as_string,
                map_to_keys=map_to_keys,
                **kwargs
            )
        else:
            message = f'Could not find any matching tag in HTML page using the following criteria: {f}'
            self.logger.info(message)
            print(message)
        return self.tournaments

    @property
    def number_of_tournaments(self):
        return len(self.tournaments)

    def _construct_tournament_header(self, information):
        """
        Constructs the dictionnary that will be used to reference
        the tournament in the final dictionnary

        Parameters
        ----------

        - information: a list of type [..., [..., ...], ..., ..., ...]

        Result
        ------

        Returns the tournament name and the constructed header

        - (tournament_name, {...})
        """

        tournament = {
            'matches': [], 
            'missing_fields': []
        }
        
        if not information:
            return None, tournament

        try:
            tour_title = information[1][0]
        except (KeyError, IndexError):
            name = country = None
            tournament.update({'missing_fields': ['name', 'country']})            
        else:
            try:
                name, country = tour_title.split(',', 1)
            except:
                # This is done in
                # order to still provide a name to the
                # tournament if none was initially catched
                name = information[:1][0]
                country = None
                tournament.update({'missing_fields': ['name', 'country']})
            tournament.update({'name': name, 'country': country})
        
        try:
            tournament['date'] = information[1][1]
        except (KeyError, IndexError):
            tournament['date'] = None
            tournament.update({'missing_fields': ['tour_date']})

        try:
            tournament['type'] = information[2]
        except (KeyError, IndexError):
            tournament['type'] = None
            tournament.update({'missing_fields': ['type']})


        try:
            tournament['surface'] = information[4]
        except (KeyError, IndexError):
            tournament['surface'] = None
            tournament.update({'missing_fields': ['surface']})


        return tournament['name'], tournament

    def _build_tournament_dict(self, **kwargs):
        """
        Create a basic empty OrderedDict
        """
        return OrderedDict(**kwargs)

    def _parse_footer(self, footer, using=None):
        """
        Parse the footer element in order to return
        the playing ranking during the tournament
        and their seeding if available
        """
        player_rank_during_tournament = {
            'rank': None,
            'entered_as': None,
            'seed_title': None
        }
        # Try to get the rank of the player
        # during the tournament -;
        rank_section = footer.find_next('span')
        rank = rank_section.find_next_sibling('span')

        # Sometimes, there is no player rank
        # but an entry type - so, this tests
        # if there is one or the other
        entry_types = ['W', 'Q']
        if rank.text.isnumeric():
            player_rank = int(rank.text)
            player_rank_during_tournament.update({
                'rank': player_rank
            })
        else:
            seed_text = self._normalize(rank.text)
            if seed_text in entry_types:
                player_rank_during_tournament.update({
                    'entered_as': seed_text
                })

        # There might also have both,
        # so check also for that
        seed_section = rank.find_next('span').find_next_sibling('span')
        if seed_section is not None:
            if not seed_section.is_empty_element:
                seed_text = self._normalize(seed_section.text)
                if seed_text in entry_types:
                    player_rank_during_tournament.update({
                        'entered_as': seed_text,
                        'seed_title': seed_section.get_attribute_list('title')[-1]
                    })
                elif seed_text.isnumeric():
                    player_rank_during_tournament.update({
                        'entered_as': int(seed_text)
                    })

        if using is not None:
            # Dynamically find the root key of the dictionnary
            # in order to update it with the rankings
            using[list(using.keys())[-1]]['ranking'] = player_rank_during_tournament
            return using
        return player_rank_during_tournament

    def _parse_tournament_header(self, header):
        """
        Parse the header for each tournaments

        Extract the tournament's name, level and other
        characteristics useful for identifying the tournament
        """
        base = self._build_tournament_dict(matches=[])
        characteristics = []
        if header is not None:
            for child in header.children:
                if child.name == 'h2':
                    # TODO: Some H2 tags have links in them
                    # and a 'title' -; maybe use that also
                    # to get tournament title with another
                    # method to parse the city from that
                    characteristics.append(child.text)

                if child is not None or child != '\n':
                    if child.name == 'div':
                        class_name = child.attrs['class']
                        if 'locdate' in str(class_name):
                            spans = child.find_all('span')
                            characteristics.append(
                                [spans[0].text, spans[1].text])

                        if 'meta' in str(class_name):
                            spans = self._filter(child.find_all('span'), 'value')
                            for span in spans:
                                characteristics.append(span.text)

            name, details = self._construct_tournament_header(characteristics)
            base.update({name: details})
            characteristics = []
        else:
            return False
        return base

    def _parse_matches(self, matches, using=None):
        """
        Parses the matches from the table
        
        Parameters
        ----------

        `matches` represents the table rows for each match
        """
        if using is None:
            base = {}
        else:
            base = using

        base_match_template = {
            'opp_name': None,
            'link': None,
            'nationality': None,
            'details': {}
        }
        base_match = base_match_template.copy()

        for _, row in enumerate(matches):
            opponent_link = row.find('a')
            if opponent_link is not None:
                base_match.update({
                    'opp_name': opponent_link.get_attribute_list('title')[-1],
                    'link': opponent_link.get_attribute_list('href')[-1],
                })

            children = list(filter(lambda x: x != '\n', row.children))
            for i, child in enumerate(children):
                if child.name == 'td':
                    if i == 0:
                        divs = child.find_all('div')
                        if divs:
                            base_match['details']['round'] = divs[-1].text
                    
                    if i == 1:
                        nationality_tag = child.find('img')
                        if nationality_tag is not None:
                            if nationality_tag.has_attr('alt'):
                                base_match['nationality'] = nationality_tag.get_attribute_list('alt')[-1]
                            else:
                                base_match['nationality'] = None
                        else:
                            base_match['nationality'] = None
                            
                    if i == 2:
                        base_match['details']['opp_rank'] = child.get_text()

                    if i == 3:
                        base_match['details']['result'] = child.get_text()
                        score = child.find_next('td').text
                        base_match['details']['score'] = score

            # Append a copy of base_match otherwise
            # base_match will continue pointing towards
            # the variable above and will keep getting cleared
            # or modidified when calling further functions on
            # thus making the final dict not valid
            base['matches'].append(base_match.copy())

            base_match.clear()
            base_match = base_match_template.copy()
            # For whatever reasons, when modifying the details
            # section of base_match, it also modifies the details
            # section of bae_match_template despite the clear().
            # This results in the same score being appended in the
            # final dictionnary and the match results being the same
            # when constructing the matches
            base_match['details'] = {}
        return base

    def _date_difference_from_today(self, d):
        """
        Calculates the difference between two dates

        Parameters
        ----------

        - `d` represents as a datetime.datetime format
        """
        current_date = datetime.datetime.now().date()
        return current_date.year - d.year

    def _finalize(self, **kwargs):
        """
        Voluntarily, the initital dictionnaries that were created by tournament
        contain the raw data with spaces and/or new lines. This section takes
        them, cleans the data within them and prepares them for final use
        """        
        pre_final_dict = self.tournaments
        tournaments = []

        # Done in order to initiate a
        # reverse countdown for iDs
        tournaments_count = len(pre_final_dict)
        self.logger.info(f'Finalizing for {tournaments_count} tournaments')

        # Some of the tournaments names are very long
        # and not really adequate for being a dictionnary
        # key. This offers the possibility to map a specific
        # retrieved tournament name to one that is more suitable
        values_to_map = {}
        if 'map_to_keys' in kwargs:
            values_to_map = kwargs.pop('map_to_keys')
            if not isinstance(values_to_map, dict):
                raise TypeError('The tournament titles to map should be a dictionnary')
        
        date_of_birth = None
        if 'date_of_birth' in kwargs:
            date_of_birth = datetime.datetime.strptime(kwargs['date_of_birth'], '%Y-%m-%d')
            kwargs.update({'age': self._date_difference_from_today(date_of_birth)})

        for i, tournament in enumerate(pre_final_dict):
            blank_dict = self._build_tournament_dict()
            try:
                matches = tournament.pop('matches')
            except:
                matches = []
            # TODO: The first array has none values.
            # Should prevent the empty array being
            # appended when parsing the matches
            # matches.pop(0)
            for key, values in tournament.items():
                if key is not None:
                    key = self._normalize(' '.join(self._deep_clean(key)), as_title=True)
                    if values_to_map:
                        try:
                            key = values_to_map[key]
                        except KeyError:
                            pass

                    blank_dict[key] = values
                    blank_dict[key].update(
                        {
                            'id': tournaments_count - i,
                            'matches': matches,
                            'name': key,
                            'country': self._normalize(values['country'], as_title=True)
                        }
                    )

                    tour_date = self._parse_date(blank_dict[key]['date'])
                    if tour_date is not None:
                        if 'date_as_string' in kwargs:
                            if kwargs['date_as_string']:
                                blank_dict[key]['date'] = str(tour_date)
                            else:
                                blank_dict[key]['date'] = tour_date
                        blank_dict[key]['year'] = tour_date.year
                    else:
                        blank_dict[key]['year'] = None

                    blank_dict[key]['ranking'] = values['ranking']

                    matches_count = len(matches)
                    for i, match in enumerate(matches):
                        match['details'] = self._deep_clean_multiple(match['details'])
                        match['id'] = matches_count - i

            tournaments.append(blank_dict)
        tournaments.append(kwargs)
        self.tournaments = tournaments
        self.logger.info('Adapting...')
        self.logger.info((f'Found and built {len(self.tournaments) - 1} tournaments'))
        self.logger.info("Call 'write_values_to_file' if you wish to output the values to a file")

    @lru_cache(maxsize=5)
    def get_matches(self):
        for tournament in self.tournaments:
            for key in tournament.keys():
                yield tournament[key]['matches']

    @property
    def get_tournaments(self):
        return self.tournaments

    def write_values_to_file(self, values=None, file_format='json', **kwargs):
        """
        Write the parsed values to a file of type JSON or CSV
        """
        if values is None:
            if self.tournaments is not None:
                values = self.tournaments
            else:
                values = {}

        new_file_name = secrets.token_hex(5)
        if 'player' in kwargs:
            if kwargs['player'] is not None:
                new_file_name = '_'.join(kwargs['player'].split(' '))

        file_to_write = os.path.join(
            BASE_DIR, 
            f'{new_file_name}.{file_format}'
        )
        with open(file_to_write, 'w') as f:
            if file_format == 'json':
                try:
                    json.dump(values, f, indent=4)
                except TypeError as e:
                    self.logger.error(
                        'Make sure "date_as_string" is set to true so that the date can be serialized correctly',
                        stack_info=True
                    )
                    raise

            if file_format == 'csv':
                writer = csv.writer(f)
                if 'header' in kwargs:
                    values.insert(0, kwargs['header'])
                writer.write_rows(values)
        self.logger.info(f'Created file {file_to_write}')

    def load(self, filename):
        """
        Load a result file and return its data
        """
        if not filename.endswith('json'):
            filename = f'{filename}.json'

        with open(f'data/{filename}', 'r') as f:
            data = json.load(f)
        self.logger.info(f'Loading {filename}')
        return Query(data)

    def loads(self, *filenames):
        """
        Load multiple JSON files

        Parameters
        ----------

            filenames (list): files to load
        """
        data = []
        concat_tournaments = []
        for name in filenames:
            data.append(self.load(name))

        for model in data:
            for tournamnent in model.tournaments:
                concat_tournaments.append(tournamnent)
        
        number_of_tournaments = len(concat_tournaments)
        for i, tournament in enumerate(concat_tournaments):
            tournament['id'] = number_of_tournaments - i
        self.tournaments = concat_tournaments


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse an HTML page for WTA matches')
    parser.add_argument('-n', '--filename', type=str, required=True, help='The HTML file to parse')
    parser.add_argument('--write', type=bool, help='Write parsed values to a JSON or CSV file')
    parser.add_argument('--filter', type=str, required=True, help='A value used to filter the html tags on the WTA page')
    parser.add_argument('--format', type=str, choices=['json', 'csv'], help='The format of the output file')

    parser.add_argument('--player', type=str, help='Name of the player to parse file for')
    parser.add_argument('--year', type=int, help='Year of the tournaments')
    parsed_arguments = parser.parse_args()
    
    scrapper = MatchScrapper(filename=parsed_arguments.filename)
    scrapper.build(
        parsed_arguments.filter, 
        player_name=parsed_arguments.player, 
        year=parsed_arguments.year
    )
    scrapper.write_values_to_file()
