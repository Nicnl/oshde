import collections


def update(base, more):
    for key, value in more.items():
        if key not in base:
            base[key] = value

        try:
            if isinstance(value, collections.Mapping):
                base[key] = update(base[key], value)
            elif isinstance(value, list):
                base[key].extend(value)
            else:
                base[key] = value
        except AttributeError:
            base[key] = value
    return base
