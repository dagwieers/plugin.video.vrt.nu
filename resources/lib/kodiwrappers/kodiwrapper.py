# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import xbmc
import xbmcplugin

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

sort_methods = dict(
    # date=xbmcplugin.SORT_METHOD_DATE,
    dateadded=xbmcplugin.SORT_METHOD_DATEADDED,
    duration=xbmcplugin.SORT_METHOD_DURATION,
    episode=xbmcplugin.SORT_METHOD_EPISODE,
    # genre=xbmcplugin.SORT_METHOD_GENRE,
    label=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
    # none=xbmcplugin.SORT_METHOD_UNSORTED,
    # FIXME: We would like to be able to sort by unprefixed title (ignore date/episode prefix)
    # title=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
    unsorted=xbmcplugin.SORT_METHOD_UNSORTED,
)

log_levels = dict(
    Quiet=0,
    Info=1,
    Verbose=2,
    Debug=3,
)


def has_socks():
    ''' Test if socks is installed, and remember this information '''
    if not hasattr(has_socks, 'installed'):
        try:
            import socks  # noqa: F401; pylint: disable=unused-variable,unused-import
            has_socks.installed = True
        except ImportError:
            has_socks.installed = False
            return None  # Detect if this is the first run
    return has_socks.installed


class KodiWrapper:

    def __init__(self, handle, url, addon):
        self._handle = handle
        self._url = url
        self._addon = addon
        self._addon_id = addon.getAddonInfo('id')
        self._max_log_level = log_levels.get(self.get_setting('max_log_level'), 3)

    def show_listing(self, list_items, sort='unsorted', ascending=True, content_type=None, cache=True):
        import xbmcgui
        listing = []

        if content_type:
            xbmcplugin.setContent(self._handle, content=content_type)

        # FIXME: Since there is no way to influence descending order, we force it here
        if not ascending:
            sort = 'unsorted'

        # Add all sort methods to GUI (start with preferred)
        xbmcplugin.addSortMethod(handle=self._handle, sortMethod=sort_methods[sort])
        for key in sorted(sort_methods):
            if key != sort:
                xbmcplugin.addSortMethod(handle=self._handle, sortMethod=sort_methods[key])

        # FIXME: This does not appear to be working, we have to order it ourselves
#        xbmcplugin.setProperty(handle=self._handle, key='sort.ascending', value='true' if ascending else 'false')
#        if ascending:
#            xbmcplugin.setProperty(handle=self._handle, key='sort.order', value=str(sort_methods[sort]))
#        else:
#            # NOTE: When descending, use unsorted
#            xbmcplugin.setProperty(handle=self._handle, key='sort.order', value=str(sort_methods['unsorted']))

        for title_item in list_items:
            list_item = xbmcgui.ListItem(label=title_item.title, thumbnailImage=title_item.art_dict.get('thumb'))
            url = self._url + '?' + urlencode(title_item.url_dict)
            list_item.setProperty(key='IsPlayable', value='true' if title_item.is_playable else 'false')

            # FIXME: This does not appear to be working, we have to order it ourselves
#            list_item.setProperty(key='sort.ascending', value='true' if ascending else 'false')
#            if ascending:
#                list_item.setProperty(key='sort.order', value=str(sort_methods[sort]))
#            else:
#                # NOTE: When descending, use unsorted
#                list_item.setProperty(key='sort.order', value=str(sort_methods['unsorted']))

            if title_item.art_dict:
                list_item.setArt(title_item.art_dict)

            if title_item.video_dict:
                list_item.setInfo(type='video', infoLabels=title_item.video_dict)

            listing.append((url, list_item, not title_item.is_playable))

        ok = xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))
        xbmcplugin.endOfDirectory(self._handle, ok, cacheToDisc=cache)

    def play(self, video):
        import xbmcgui
        play_item = xbmcgui.ListItem(path=video.stream_url)
        play_item.setProperty('inputstream.adaptive.max_bandwidth', str(self.get_max_bandwidth() * 1000))
        play_item.setProperty('network.bandwidth', str(self.get_max_bandwidth() * 1000))
        if video.stream_url is not None and video.use_inputstream_adaptive:
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            play_item.setMimeType('application/dash+xml')
            play_item.setContentLookup(False)
            if video.license_key is not None:
                import inputstreamhelper
                is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
                if is_helper.check_inputstream():
                    play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    play_item.setProperty('inputstream.adaptive.license_key', video.license_key)

        subtitles_visible = self.get_setting('showsubtitles') == 'true'
        # Separate subtitle url for hls-streams
        if subtitles_visible and video.subtitle_url is not None:
            self.log_notice('Subtitle URL: ' + video.subtitle_url)
            play_item.setSubtitles([video.subtitle_url])

        xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)
        while not xbmc.Player().isPlaying() and not xbmc.Monitor().abortRequested():
            xbmc.sleep(100)
        xbmc.Player().showSubtitles(subtitles_visible)

    def show_ok_dialog(self, title, message):
        import xbmcgui
        xbmcgui.Dialog().ok(self._addon.getAddonInfo('name'), title, message)

    def set_locale(self):
        import locale
        locale_lang = self.get_global_setting('locale.language').split('.')[-1]
        try:
            # NOTE: This only works if the platform supports the Kodi configured locale
            locale.setlocale(locale.LC_ALL, locale_lang)
        except Exception as e:
            self.log_notice(e, 'Verbose')

    def get_localized_string(self, string_id):
        return self._addon.getLocalizedString(string_id)

    def get_localized_dateshort(self):
        return xbmc.getRegion('dateshort')

    def get_localized_datelong(self):
        return xbmc.getRegion('datelong')

    def get_setting(self, setting_id):
        return self._addon.getSetting(setting_id)

    def set_setting(self, setting_id, setting_value):
        return self._addon.setSetting(setting_id, setting_value)

    def open_settings(self):
        self._addon.openSettings()

    def get_global_setting(self, setting):
        import json
        json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": {"setting": "%s"}, "id": 1}' % setting)
        return json.loads(json_result).get('result', dict()).get('value')

    def get_max_bandwidth(self):
        vrtnu_max_bandwidth = int(self.get_setting('max_bandwidth'))
        global_max_bandwidth = int(self.get_global_setting('network.bandwidth'))
        if vrtnu_max_bandwidth != 0 and global_max_bandwidth != 0:
            return min(vrtnu_max_bandwidth, global_max_bandwidth)
        if vrtnu_max_bandwidth != 0:
            return vrtnu_max_bandwidth
        if global_max_bandwidth != 0:
            return global_max_bandwidth
        return 0

    def get_proxies(self):
        usehttpproxy = self.get_global_setting('network.usehttpproxy')
        if usehttpproxy is False:
            return None

        httpproxytype = self.get_global_setting('network.httpproxytype')

        socks_supported = has_socks()
        if httpproxytype != 0 and not socks_supported:
            # Only open the dialog the first time (to avoid multiple popups)
            if socks_supported is None:
                message = self.get_localized_string(30061)
                self.show_ok_dialog('', message)
            return None

        proxy_types = ['http', 'socks4', 'socks4a', 'socks5', 'socks5h']
        if 0 <= httpproxytype <= 5:
            httpproxyscheme = proxy_types[httpproxytype]
        else:
            httpproxyscheme = 'http'

        httpproxyserver = self.get_global_setting('network.httpproxyserver')
        httpproxyport = self.get_global_setting('network.httpproxyport')
        httpproxyusername = self.get_global_setting('network.httpproxyusername')
        httpproxypassword = self.get_global_setting('network.httpproxypassword')

        if httpproxyserver and httpproxyport and httpproxyusername and httpproxypassword:
            proxy_address = '%s://%s:%s@%s:%s' % (httpproxyscheme, httpproxyusername, httpproxypassword, httpproxyserver, httpproxyport)
        elif httpproxyserver and httpproxyport and httpproxyusername:
            proxy_address = '%s://%s@%s:%s' % (httpproxyscheme, httpproxyusername, httpproxyserver, httpproxyport)
        elif httpproxyserver and httpproxyport:
            proxy_address = '%s://%s:%s' % (httpproxyscheme, httpproxyserver, httpproxyport)
        elif httpproxyserver:
            proxy_address = '%s://%s' % (httpproxyscheme, httpproxyserver)
        else:
            return None

        return dict(http=proxy_address, https=proxy_address)

    # Note: InputStream Adaptive is not pre-installed on Windows and in some cases users can uninstall it
    def has_inputstream_adaptive_installed(self):
        return xbmc.getCondVisibility('System.HasAddon("{0}")'.format('inputstream.adaptive')) == 1

    def can_play_drm(self):
        kodi_version = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
        return kodi_version > 17

    def get_userdata_path(self):
        return xbmc.translatePath(self._addon.getAddonInfo('profile'))

    def get_addon_path(self):
        return xbmc.translatePath(self._addon.getAddonInfo('path'))

    def get_path(self, path):
        return xbmc.translatePath(path)

    def make_dir(self, path):
        import xbmcvfs
        xbmcvfs.mkdir(path)

    def check_if_path_exists(self, path):
        import xbmcvfs
        return xbmcvfs.exists(path)

    def open_path(self, path):
        import json
        return json.loads(open(path, 'r').read())

    def delete_path(self, path):
        import xbmcvfs
        return xbmcvfs.delete(path)

    def log_notice(self, message, log_level='Info'):
        ''' Log info messages to Kodi '''
        if log_levels.get(log_level, 0) <= self._max_log_level:
            xbmc.log(msg='[%s] %s' % (self._addon_id, message), level=xbmc.LOGNOTICE)

    def log_error(self, message, log_level='Info'):
        ''' Log error messages to Kodi '''
        xbmc.log(msg='[%s] %s' % (self._addon_id, message), level=xbmc.LOGERROR)
