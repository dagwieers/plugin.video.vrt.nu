# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Unit tests for ApiHelper functionality"""

# pylint: disable=invalid-name

import sys
import kopy.xbmc
import kopy.xbmcaddon
import kopy.xbmcextra
import kopy.xbmcgui
import kopy.xbmcplugin
import kopy.xbmcvfs
sys.modules['xbmc'] = kopy.xbmc
sys.modules['xbmcaddon'] = kopy.xbmcaddon
sys.modules['xbmcextra'] = kopy.xbmcextra
sys.modules['xbmcgui'] = kopy.xbmcgui
sys.modules['xbmcplugin'] = kopy.xbmcplugin
sys.modules['xbmcvfs'] = kopy.xbmcvfs
