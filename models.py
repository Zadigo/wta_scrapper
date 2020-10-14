import pandas

class Queryset:
    """
    Contains the data from the JSON file and
    after having reconstructed the data so that
    it can be read by a DataFrame

    Parameters
    ----------

        data (list): list of items


    Returns
    -------

        (DataFrame): a pandas DataFrame
    """
    def __init__(self, data):
        self.tournaments = data
        self.matches = []

    def _build_columns(self):
        return {}

    def _get_sample_data(self, data: list=None):
        """
        Get a sample dictionnary from the data
        in order to create a dictionnary with the
        result's keys
        """
        if data is not None:
            return data[-0]
        keys = list(self.tournaments[0].keys())
        return self.tournaments[0][keys[0]]

    def _get_keys(self, values: dict=None):
        if values is not None:
            return values.keys()
        return list(self.tournaments.keys())

    def _construct_columns(self, sample_item: dict, dict_to_update: dict, exclude=[]):
        """
        Adds the keys from a from sample dictionnay to the one that
        needs updating
        """
        keys = list(sample_item.keys())
        for key in keys:
            if key not in exclude:
                dict_to_update[key] = []
        return dict_to_update

    def _construct_tournaments(self, tournaments, exclude=['matches', 'ranking', 'missing_fields']):
        columns = self._build_columns()
        updated_dict = self._construct_columns(
            self._get_sample_data(),
            columns,
            exclude=exclude
        )
        tournaments.pop(-1)
        populated_dict = self._populate_columns(tournaments, updated_dict)
        return pandas.DataFrame(populated_dict)

    def _construct_matches(self, tournaments, df_columns=[]):
        """
        Build a dataframe using the matches as a basis
        from the result file

        Parameters
        ----------

            tournaments (list): a list of tournaments

        Returns
        -------

            (dataframe): a pandas dataframe
        """
        columns = self._build_columns()
        list_of_matches = []
        tournaments.pop(-1)
        for tournament in tournaments:
            for _, values in tournament.items():
                matches = values.pop('matches')
                ranking = values.pop('ranking')
                for match in matches:
                    details = match.pop('details')

                    new_dict = {
                        **match,
                        **values,
                        **details,
                        **ranking,
                    }
                    list_of_matches.append(new_dict)
        columns = self._construct_columns(
            self._get_sample_data(data=list_of_matches), columns
        )
        result = self._populate(list_of_matches, columns)
        if df_columns:
            return result[df_columns]
        return result

    def _populate(self, data: list, dict_to_update: dict, exclude=[]):
        keys = self._get_keys(data[-0])
        for _, item in enumerate(data):
            for key in keys:
                if key not in exclude:
                    dict_to_update[key].append(item[key])
        return pandas.DataFrame(dict_to_update)

    def _populate_columns(self, data: list, dict_to_update: dict, keys=None):
        if keys is None:
            keys = list(dict_to_update.keys())
        for item in data:
            for _, values in item.items():
                for key in keys:
                    dict_to_update[key].append(values[key])

                for other_key, items in values.items():
                    if not isinstance(items, (dict, list)):
                        if other_key not in dict_to_update.keys():
                            dict_to_update[other_key].append(values[other_key])

        return dict_to_update

    def copy(self):
        new_queryset = self.__class__(self.tournaments)
        return new_queryset


class Query(Queryset):
    def __init__(self, dict_or_list, name=None, matches=False):
        super().__init__(dict_or_list)

    def get_matches(self, columns=[]):
        """
        Return a set of matches as dataframe

        Parameters

            columns (list, optional): columns to return. Defaults to [].

        Returns

            (dataframe): pandas dataframe object
        """
        return self._construct_matches(self.tournaments, df_columns=columns)

    @property
    def get_tournaments(self):
        return self._construct_tournaments(self.tournaments)

    @property
    def get_scores(self):
        return self.get_matches(columns=['score'])
