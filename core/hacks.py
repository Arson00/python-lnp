#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DFHack management."""

import collections
import filecmp
import os
import shutil
import sys

from . import log, paths
from .lnp import lnp


def open_dfhack_readme():
    """Open the DFHack Readme in the default browser."""
    from . import launcher
    index = paths.get('df', 'hack', 'docs', 'index.html')
    if os.path.isfile(index):
        launcher.open_file(index)
    else:
        launcher.open_url('https://dfhack.readthedocs.org')


def read_hacks():
    """Reads which hacks are enabled."""
    hacklines = []
    for init_file in ('dfhack', 'onLoad', 'onMapLoad'):
        try:
            with open(paths.get('dfhack_config', init_file + '_PyLNP.init'),
                      encoding='latin1') as f:
                hacklines.extend(l.strip() for l in f.readlines())
        except IOError:
            log.debug(init_file + '_PyLNP.init not found.')
    return {name: hack for name, hack in get_hacks().items()
            if hack['command'] in hacklines}


def is_dfhack_enabled():
    """Returns YES if DFHack should be used."""
    if sys.platform == 'win32':
        if 'dfhack' not in lnp.df_info.variations:
            return False
        sdl = paths.get('df', 'SDL.dll')
        sdlreal = paths.get('df', 'SDLreal.dll')
        if not os.path.isfile(sdlreal):
            return False
        return not filecmp.cmp(sdl, sdlreal, 0)
    return lnp.userconfig.get_value('use_dfhack', True)


def toggle_dfhack():
    """Toggles the use of DFHack."""
    if sys.platform == 'win32':
        if 'dfhack' not in lnp.df_info.variations:
            return
        sdl = paths.get('df', 'SDL.dll')
        sdlhack = paths.get('df', 'SDLhack.dll')
        sdlreal = paths.get('df', 'SDLreal.dll')
        if is_dfhack_enabled():
            shutil.copyfile(sdl, sdlhack)
            shutil.copyfile(sdlreal, sdl)
        else:
            shutil.copyfile(sdl, sdlreal)
            shutil.copyfile(sdlhack, sdl)
    else:
        lnp.userconfig['use_dfhack'] = not lnp.userconfig.get_value(
            'use_dfhack', True)
        lnp.save_config()


def get_hacks():
    """Returns dict of available hacks."""
    return collections.OrderedDict(sorted(
        lnp.config.get_dict('dfhack').items(), key=lambda t: t[0]))


def get_hack(title):
    """
    Returns the hack titled <title>, or None if this does not exist.

    Args:
        title: the title of the hack.
    """
    try:
        return get_hacks()[title]
    except KeyError:
        log.d('No hack configured with name ' + title)
        return None


def toggle_hack(name):
    """
    Toggles the hack <name>.

    Args:
        name: the name of the hack to toggle.

    Returns:
        True if the hack is now enabled,
        False if the hack is now disabled,
        None on error (no change in status)
    """
    # Setup - get the hack, which file, and validate
    hack = get_hack(name)
    init_file = hack.get('file', 'dfhack')
    if init_file not in ('dfhack', 'onLoad', 'onMapLoad'):
        log.e('Illegal file configured for hack %s; must be one of '
              '"dfhack", "onLoad", "onMapLoad"', name)
        return None
    # Get the enabled hacks for this file, and toggle our state
    hacks = {name: h for name, h in read_hacks().items()
             if h.get('file', 'dfhack') == init_file}
    is_enabled = False
    if not hacks.pop(name, False):
        is_enabled = True
        hacks[name] = hack
    # Write back to the file
    fname = paths.get('dfhack_config', init_file + '_PyLNP.init')
    log.i('Rebuilding {} with the enabled hacks'.format(fname))
    lines = ['# {}\n# {}\n{}\n\n'.format(
        k, h['tooltip'].replace('\n', '\n#'), h['command'])
             for k, h in hacks.items()]
    if lines:
        with open(fname, 'w', encoding='latin1') as f:
            f.write('# Generated by PyLNP\n\n')
            f.writelines(lines)
    elif os.path.isfile(fname):
        os.remove(fname)
    return is_enabled
