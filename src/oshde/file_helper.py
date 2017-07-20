import os

allowed_characters = [
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
