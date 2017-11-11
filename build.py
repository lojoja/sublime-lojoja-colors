#! /usr/bin/env python3

from codecs import open
import copy
import json
from pathlib import Path
import re
import sys

SOURCE_PATH = Path('source')
SCHEMES_FILE = Path(SOURCE_PATH, 'schemes.json')
COLORS_FILE = Path(SOURCE_PATH, 'colors.json')
TEMPLATE_FILE = Path(SOURCE_PATH, 'template.json')


def load_data(file):
    """
    Load json data.

    Comments are allowed in source data.
    Comments must start with "//" and be the only content on the line.
    """
    pattern = re.compile(r'^\s*//.*$', re.M)
    data = None

    try:
        with open(file, mode='rb', encoding='utf-8') as f:
            raw_data = f.read()
            data = json.loads(re.sub(pattern, '', raw_data))
    except ValueError:
        raise ValueError('Failed to parse file: "{0}"'.format(file))

    return data


def save_data(data, filename):
    """Save color scheme."""
    try:
        with open(filename, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4))
    except ValueError:
        raise ValueError('Failed to create file: "{0}"'.format(filename))


def main():
    schemes = load_data(SCHEMES_FILE)
    colors = load_data(COLORS_FILE)
    template = load_data(TEMPLATE_FILE)

    for name, data in schemes.items():
        shade = colors['shade'][data['shade']]
        palette = colors['palette'][data['palette']]

        # Create a new color scheme
        color_scheme = copy.deepcopy(template)

        # Set basic information
        color_scheme.update({
            'name': name,
            'author': data['author']
        })

        # Set variables
        variables = colors['base']
        variables.update(shade['variables'])
        variables.update(palette)
        color_scheme['variables'].update(variables)

        # Set global styles
        color_scheme['globals'].update(shade['globals'])

        # Save scheme
        filename = '{0}.sublime-color-scheme'.format(name)
        save_data(color_scheme, filename)

if __name__ == '__main__':
    sys.exit(main())
