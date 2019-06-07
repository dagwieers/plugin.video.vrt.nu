# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# pylint: disable=missing-docstring

from __future__ import absolute_import, division, print_function, unicode_literals
import unittest

from resources.lib import favorites, kodiwrapper, tokenresolver

xbmc = __import__('xbmc')
xbmcaddon = __import__('xbmcaddon')
xbmcgui = __import__('xbmcgui')
xbmcplugin = __import__('xbmcplugin')
xbmcvfs = __import__('xbmcvfs')

xbmcaddon.ADDON_SETTINGS['usefavorites'] = 'true'


class TestFavorites(unittest.TestCase):

    _kodi = kodiwrapper.KodiWrapper(None, 'plugin://plugin.video.vrt.nu')
    _tokenresolver = tokenresolver.TokenResolver(_kodi)
    _favorites = favorites.Favorites(_kodi, _tokenresolver)

    def test_follow_unfollow(self):
        program = 'Winteruur'
        program_path = '/vrtnu/a-z/winteruur/'
        self._favorites.follow(program, program_path)
        self.assertTrue(self._favorites.is_favorite(program_path))

        self._favorites.unfollow(program, program_path)
        self.assertFalse(self._favorites.is_favorite(program_path))

        self._favorites.follow(program, program_path)
        self.assertTrue(self._favorites.is_favorite(program_path))

    def test_names(self):
        names = self._favorites.names()
        self.assertTrue(names)
        print(names)

    def test_titles(self):
        titles = self._favorites.titles()
        self.assertTrue(titles)
        print(sorted(titles))


if __name__ == '__main__':
    unittest.main()
