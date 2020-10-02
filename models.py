import pandas

class Queryset:
    def __init__(self, data):
        self.tournaments = data

    def copy(self):
        new_queryset = self.__class__(self.tournaments)
        return new_queryset

    def get(self, **kwargs):
        queryset = self.copy()
        return queryset

    def filter(self, **kwargs):
        queryset = self.copy()
        return queryset

    def values_list(self, *args, flat=False):
        queryset = self.copy()
        return queryset


class Tournament(Queryset):
    def __init__(self, dict_or_list, name=None):
        tournaments = dict_or_list
        if isinstance(tournaments, list):
            tournaments = tournaments[0]

        super().__init__(tournaments)

        names, values = self._deconstruct(tournaments)

        df = pandas.DataFrame()
        for i, value in enumerate(values):
            matches = value.pop('matches')
            new_class = self.copy(list(names)[i], list(values)[i])
            new_class.matches = matches
            for key, value in value.items():
                setattr(new_class, key, value)
            self.tournaments.append(new_class)
        # matches = values.pop('matches')

        # self.name = name
        # self.tournament = df.from_dict(values, orient='columns')
        # self.matches = df.from_dict(matches, orient='columns')
        # self.tournaments = list(values.keys())

    def __str__(self):
        if self.name:
            return f'{self.name}([{self.matches.shape}])'
        return f'{self.__class__.__name__}([{self.matches.shape}])'

    def __repr__(self):
        return self.__str__()

    @property
    def matches(self):
        return self.matches

    @property
    def scores(self):
        pass

    def _deconstruct(self, values):
        keys = values.keys()
        values = values.values()
        return keys, values

    @classmethod
    def copy(cls, name, matches=[]):
        attrs = {
            'name': name,
            'matches': matches
        }
        klass = type(name, (), attrs)
        if ' ' in name:
            name = name.replace(' ', '')
        setattr(klass, '__qualname__', name)
        setattr(klass, '__repr__', f"<class '{name}'>")
        # values_to_copy = ['scores', 'matches']
        # klass_dict = self.__dict__.copy()
        # for key, value in klass_dict.items():
        #     if key in values_to_copy:
        #         setattr(klass, key, value)
        return klass
