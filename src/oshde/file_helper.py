import os

allowed_characters = [
    '0', '1', '2', '3', '4', '5', '6',
    '7', '8', '9',

    'a', 'b', 'c', 'd', 'e', 'f', 'g',
    'h', 'i', 'j', 'k', 'l', 'm', 'n',
    'o', 'p', 'q', 'r', 's', 't', 'u',
    'v', 'w', 'x', 'y', 'z'
]


def list_dirs(path):
    return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]


def dockerize_domain_dir(domain_dir):
    output = ''
    for char in domain_dir:
        if char in allowed_characters:
            output += char
        elif not output.endswith('-'):
            output += '-'
    return output
