import json
import os
import secrets
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, 'data')

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


def write_new_file(values, update_for, filename=secrets.token_hex(5)):
    """
    Quickly write values to a file

    Parameters

        values (list): list of values to write
        update_for (str): the name of the file from which the data was updated
        filename (str, optional): file name. Defaults to secrets.hex_token(5).

    Returns

        bool: True or False
    """
    file_name = f'{filename}_updated_from_{update_for}.json'
    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, 'w') as f:
        json.dump(values, f, indent=4)
    return True
