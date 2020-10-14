import os
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES = os.listdir(os.path.join(BASE_DIR, 'html'))

@lru_cache(maxsize=10)
def autodiscover():
    """
    Autodiscover files in the HTML folder of the application
    """
    def wrapper(filename=None):
        if filename is not None:
            if filename in TEMPLATES:
                _file = TEMPLATES[TEMPLATES.index(filename)]
                return os.path.join(BASE_DIR, 'html', _file)
        raise FileNotFoundError(
            f'The file you are looking for does not exist. {", ".join(TEMPLATES)}')
    return wrapper


def get_data_file(name):
    data_path = os.path.join(BASE_DIR, 'data')
    return os.path.join(data_path, name)
