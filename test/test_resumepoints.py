# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# pylint: disable=invalid-name,missing-docstring

from __future__ import absolute_import, division, print_function, unicode_literals
import unittest
from addon import kodi
from apihelper import ApiHelper
from favorites import Favorites
from resumepoints import ResumePoints

xbmc = __import__('xbmc')
xbmcaddon = __import__('xbmcaddon')
xbmcgui = __import__('xbmcgui')
xbmcplugin = __import__('xbmcplugin')
xbmcvfs = __import__('xbmcvfs')

xbmcaddon.ADDON_SETTINGS['plugin.video.vrt.nu']['useresumepoints'] = 'true'


class TestResumePoints(unittest.TestCase):

    _favorites = Favorites(kodi)
    _resumepoints = ResumePoints(kodi)
    _apihelper = ApiHelper(kodi, _favorites, _resumepoints)

    # Update resume_points.json
    _resumepoints.get_resumepoints(ttl=0)

    def test_update_watchlist(self):
        self._resumepoints.get_resumepoints(ttl=0)
        assetuuid, first_entry = next(iter(self._resumepoints._resumepoints.items()))  # pylint: disable=protected-access
        print('%s = %s' % (assetuuid, first_entry))
        url = first_entry.get('value').get('url')
        self._resumepoints.watchlater(uuid=assetuuid, title='Foo bar', url=url)
        self._resumepoints.unwatchlater(uuid=assetuuid, title='Foo bar', url=url)
        self._resumepoints.get_resumepoints(ttl=0)
        assetuuid, first_entry = next(iter(self._resumepoints._resumepoints.items()))  # pylint: disable=protected-access
        print('%s = %s' % (assetuuid, first_entry))


if __name__ == '__main__':
    unittest.main()
