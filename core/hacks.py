#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DFHack management."""
from __future__ import print_function, unicode_literals, absolute_import

import sys, os, shutil, filecmp
# pylint:disable=redefined-builtin
from io import open
from . import paths, log
from .lnp import lnp

def read_hacks():
    """Reads which hacks are enabled."""
    hacklines = []
    for init_file in ('dfhack', 'onLoad', 'onMapLoad'):
        try:
            with open(paths.get('df', init_file + '_PyLNP.init'), 
                      encoding='latin1') as f:
                hacklines.extend(l.strip() for l in f.readlines())
        except IOError:
            log.debug(init_file + '_PyLNP.init not found.')
    for h in get_hacks().values():
        h['enabled'] = h['command'] in hacklines

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
    else:
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
    return lnp.config.get_dict('dfhack')

def get_hack(title):
    """
    Returns the hack titled <title>, or None if this does not exist.

    Params:
        title
            The title of the hack.
    """
    try:
        return get_hacks()[title]
    except KeyError:
        log.d('No hack configured with name ' + title)
        return None

def toggle_hack(name):
    """
    Toggles the hack <name>.

    Params:
        name
            The name of the hack to toggle.
    """
    get_hack(name)['enabled'] = not get_hack(name)['enabled']
    lnp.config.save_data()
    rebuild_hacks()

def rebuild_hacks():
    """Rebuilds *_PyLNP.init files with the enabled hacks."""
    log.i('Rebuilding dfhack_PyLNP.init files with the enabled hacks')
    for init_file in ('dfhack', 'onLoad', 'onMapLoad'):
        fname = os.path.isfile(paths.get('df', init_file + '_PyLNP.init'))
        lines = []
        for k, h in get_hacks().items():
            if h['enabled'] and h.get('file', 'dfhack') == init_file:
                lines.append('# {}\n# {}\n{}\n\n'.format(
                    k, h['tooltip'].replace('\n', '\n#'), h['command']))
        if lines:
            with open(fname, 'w', encoding='latin1') as f:
                f.write('# Generated by PyLNP\n\n')
                f.writelines(lines)
        elif os.path.isfile(fname):
            os.remove(fname)
