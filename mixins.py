import re
import datetime

class Mixins:
    @staticmethod
    def _parse_date(d):
        regex = r'(?<=\-)(?P<month>\w+)\s?(?P<day>\d+)(?:\,\s)(?P<year>\d+)$'
        has_date = re.search(regex, d)
        if has_date:
            months = {
                'Jan': 1,
                'Feb': 2,
                'Mar': 3,
                'Apr': 4,
                'May': 5,
                'Jun': 6,
                'Jul': 7,
                'Aug': 8,
                'Sep': 9,
                'Oct': 10,
                'Nov': 11,
                'Dec': 12
            }
            month, day, year = has_date.groups()
            return datetime.date(int(year), int(months[month]), int(day))
        return None

    @staticmethod
    def _deep_clean(text):
        """
        Takes out all the new lines within a character and
        strips all the spaces

        Result
        ------

        Returns a list of cleaned values: [..., ...]
        """
        if text is not None:
            # By mistake a dict can be passed
            # here and in that case we have to
            # protect against that
            if not isinstance(text, dict):
                new_text = re.sub('\n', ' ', text)
                list_values = new_text.split(' ')
                return [item for item in list_values if item != '']
            else:
                return text
        else:
            return text

    def _deep_clean_multiple(self, items: dict):
        keys = items.keys()
        for key in keys:
            new_value = ' '.join(self._deep_clean(items[key]))
            items[key] = new_value
        return items

    @staticmethod
    def _filter(items, criteria, attr='class'):
        """
        Return a set of items based on certain criteria
        """
        result = []
        for item in items:
            if item.has_attr(attr):
                class_attrs = item.attrs['class']
                if criteria in str(class_attrs[0]):
                    result.append(item)
        return result if result else False

    @staticmethod
    def _normalize(text: str, as_title=True):
        if text is None:
            return None

        text = text.strip()
        if as_title:
            return text.lower().title()
        return text
