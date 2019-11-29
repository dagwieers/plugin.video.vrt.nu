# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' All functionality that requires Kodi imports '''

from __future__ import absolute_import, division, unicode_literals
from contextlib import contextmanager
import xbmc
import xbmcplugin
from statichelper import from_unicode, to_unicode

SORT_METHODS = dict(
    # date=xbmcplugin.SORT_METHOD_DATE,
    dateadded=xbmcplugin.SORT_METHOD_DATEADDED,
    duration=xbmcplugin.SORT_METHOD_DURATION,
    episode=xbmcplugin.SORT_METHOD_EPISODE,
    # genre=xbmcplugin.SORT_METHOD_GENRE,
    # label=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
    label=xbmcplugin.SORT_METHOD_LABEL,
    # none=xbmcplugin.SORT_METHOD_UNSORTED,
    # FIXME: We would like to be able to sort by unprefixed title (ignore date/episode prefix)
    # title=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
    unsorted=xbmcplugin.SORT_METHOD_UNSORTED,
)

WEEKDAY_LONG = {
    '0': xbmc.getLocalizedString(17),
    '1': xbmc.getLocalizedString(11),
    '2': xbmc.getLocalizedString(12),
    '3': xbmc.getLocalizedString(13),
    '4': xbmc.getLocalizedString(14),
    '5': xbmc.getLocalizedString(15),
    '6': xbmc.getLocalizedString(16),
}

MONTH_LONG = {
    '01': xbmc.getLocalizedString(21),
    '02': xbmc.getLocalizedString(22),
    '03': xbmc.getLocalizedString(23),
    '04': xbmc.getLocalizedString(24),
    '05': xbmc.getLocalizedString(25),
    '06': xbmc.getLocalizedString(26),
    '07': xbmc.getLocalizedString(27),
    '08': xbmc.getLocalizedString(28),
    '09': xbmc.getLocalizedString(29),
    '10': xbmc.getLocalizedString(30),
    '11': xbmc.getLocalizedString(31),
    '12': xbmc.getLocalizedString(32),
}

WEEKDAY_SHORT = {
    '0': xbmc.getLocalizedString(47),
    '1': xbmc.getLocalizedString(41),
    '2': xbmc.getLocalizedString(42),
    '3': xbmc.getLocalizedString(43),
    '4': xbmc.getLocalizedString(44),
    '5': xbmc.getLocalizedString(45),
    '6': xbmc.getLocalizedString(46),
}

MONTH_SHORT = {
    '01': xbmc.getLocalizedString(51),
    '02': xbmc.getLocalizedString(52),
    '03': xbmc.getLocalizedString(53),
    '04': xbmc.getLocalizedString(54),
    '05': xbmc.getLocalizedString(55),
    '06': xbmc.getLocalizedString(56),
    '07': xbmc.getLocalizedString(57),
    '08': xbmc.getLocalizedString(58),
    '09': xbmc.getLocalizedString(59),
    '10': xbmc.getLocalizedString(60),
    '11': xbmc.getLocalizedString(61),
    '12': xbmc.getLocalizedString(62),
}


class SafeDict(dict):
    ''' A safe dictionary implementation that does not break down on missing keys '''
    def __missing__(self, key):
        ''' Replace missing keys with the original placeholder '''
        return '{' + key + '}'


def addon_icon():
    ''' Cache and return add-on icon '''
    if not hasattr(addon_icon, 'cached'):
        from xbmcaddon import Addon
        addon_icon.cached = to_unicode(Addon().getAddonInfo('icon'))
    return getattr(addon_icon, 'cached')


def addon_id():
    ''' Cache and return add-on ID '''
    if not hasattr(addon_id, 'cached'):
        from xbmcaddon import Addon
        addon_id.cached = to_unicode(Addon().getAddonInfo('id'))
    return getattr(addon_id, 'cached')


def addon_fanart():
    ''' Cache and return add-on fanart '''
    if not hasattr(addon_fanart, 'cached'):
        from xbmcaddon import Addon
        addon_fanart.cached = to_unicode(Addon().getAddonInfo('fanart'))
    return getattr(addon_fanart, 'cached')


def addon_name():
    ''' Cache and return add-on name '''
    if not hasattr(addon_name, 'cached'):
        from xbmcaddon import Addon
        addon_name.cached = to_unicode(Addon().getAddonInfo('name'))
    return getattr(addon_name, 'cached')


def addon_path():
    ''' Cache and return add-on path '''
    if not hasattr(addon_path, 'cached'):
        from xbmcaddon import Addon
        addon_path.cached = to_unicode(Addon().getAddonInfo('path'))
    return getattr(addon_path, 'cached')


def addon_profile():
    ''' Cache and return add-on profile '''
    if not hasattr(addon_profile, 'cached'):
        from xbmcaddon import Addon
        addon_profile.cached = to_unicode(xbmc.translatePath(Addon().getAddonInfo('profile')))
    return getattr(addon_profile, 'cached')


def url_for(name, *args, **kwargs):
    ''' Wrapper for routing.url_for() to lookup by name '''
    import addon
    return addon.plugin.url_for(getattr(addon, name), *args, **kwargs)


def show_listing(list_items, category=None, sort='unsorted', ascending=True, content=None, cache=None, selected=None):
    ''' Show a virtual directory in Kodi '''
    from addon import plugin
    from xbmcgui import ListItem

    set_property('container.url', 'plugin://' + addon_id() + plugin.path)
    xbmcplugin.setPluginFanart(handle=plugin.handle, image=from_unicode(addon_fanart()))

    usemenucaching = get_setting('usemenucaching', 'true') == 'true'
    if cache is None:
        cache = usemenucaching
    elif usemenucaching is False:
        cache = False

    if content:
        # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
        xbmcplugin.setContent(plugin.handle, content=content)

    # Jump through hoops to get a stable breadcrumbs implementation
    category_label = ''
    if category:
        if not content:
            category_label = 'VRT NU / '
        if plugin.path.startswith(('/favorites/', '/resumepoints/')):
            category_label += localize(30428) + ' / '  # My
        if isinstance(category, int):
            category_label += localize(category)
        else:
            category_label += category
    elif not content:
        category_label = 'VRT NU'
    xbmcplugin.setPluginCategory(handle=plugin.handle, category=category_label)

    # FIXME: Since there is no way to influence descending order, we force it here
    if not ascending:
        sort = 'unsorted'

    # NOTE: When showing tvshow listings and 'showoneoff' was set, force 'unsorted'
    if get_setting('showoneoff', 'true') == 'true' and sort == 'label' and content == 'tvshows':
        sort = 'unsorted'

    # Add all sort methods to GUI (start with preferred)
    xbmcplugin.addSortMethod(handle=plugin.handle, sortMethod=SORT_METHODS[sort])
    for key in sorted(SORT_METHODS):
        if key != sort:
            xbmcplugin.addSortMethod(handle=plugin.handle, sortMethod=SORT_METHODS[key])

    # FIXME: This does not appear to be working, we have to order it ourselves
#    xbmcplugin.setProperty(handle=plugin.handle, key='sort.ascending', value='true' if ascending else 'false')
#    if ascending:
#        xbmcplugin.setProperty(handle=plugin.handle, key='sort.order', value=str(SORT_METHODS[sort]))
#    else:
#        # NOTE: When descending, use unsorted
#        xbmcplugin.setProperty(handle=plugin.handle, key='sort.order', value=str(SORT_METHODS['unsorted']))

    listing = []
    for title_item in list_items:
        # Three options:
        #  - item is a virtual directory/folder (not playable, path)
        #  - item is a playable file (playable, path)
        #  - item is non-actionable item (not playable, no path)
        is_folder = bool(not title_item.is_playable and title_item.path)
        is_playable = bool(title_item.is_playable and title_item.path)

        list_item = ListItem(label=title_item.title)

        if title_item.prop_dict:
            # FIXME: The setProperties method is new in Kodi18, so we cannot use it just yet.
            # list_item.setProperties(values=title_item.prop_dict)
            for key, value in list(title_item.prop_dict.items()):
                list_item.setProperty(key=key, value=str(value))
        list_item.setProperty(key='IsInternetStream', value='true' if is_playable else 'false')
        list_item.setProperty(key='IsPlayable', value='true' if is_playable else 'false')

        # FIXME: The setIsFolder method is new in Kodi18, so we cannot use it just yet.
        # list_item.setIsFolder(is_folder)

        if title_item.art_dict:
            list_item.setArt(dict(fanart=addon_fanart()))
            list_item.setArt(title_item.art_dict)

        if title_item.info_dict:
            # type is one of: video, music, pictures, game
            list_item.setInfo(type='video', infoLabels=title_item.info_dict)

        if title_item.stream_dict:
            # type is one of: video, audio, subtitle
            list_item.addStreamInfo('video', title_item.stream_dict)

        if title_item.context_menu:
            list_item.addContextMenuItems(title_item.context_menu)

        url = None
        if title_item.path:
            url = title_item.path

        listing.append((url, list_item, is_folder))

    # Jump to specific item
    if selected is not None:
        pass
#        from xbmcgui import getCurrentWindowId, Window
#        wnd = Window(getCurrentWindowId())
#        wnd.getControl(wnd.getFocusId()).selectItem(selected)

    succeeded = xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle, succeeded, updateListing=False, cacheToDisc=cache)


def play(stream, video=None):
    ''' Create a virtual directory listing to play its only item '''
    try:  # Python 3
        from urllib.parse import unquote
    except ImportError:  # Python 2
        from urllib2 import unquote

    from addon import plugin
    from xbmcgui import ListItem
    play_item = ListItem(path=stream.stream_url)
    if video and hasattr(video, 'info_dict'):
        play_item.setProperty('subtitle', video.title)
        play_item.setArt(video.art_dict)
        play_item.setInfo(
            type='video',
            infoLabels=video.info_dict
        )
    play_item.setProperty('inputstream.adaptive.max_bandwidth', str(get_max_bandwidth() * 1000))
    play_item.setProperty('network.bandwidth', str(get_max_bandwidth() * 1000))
    if stream.stream_url is not None and stream.use_inputstream_adaptive:
        play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
        play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        play_item.setMimeType('application/dash+xml')
        play_item.setContentLookup(False)
        if stream.license_key is not None:
            import inputstreamhelper
            is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
            if is_helper.check_inputstream():
                play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                play_item.setProperty('inputstream.adaptive.license_key', stream.license_key)

    subtitles_visible = get_setting('showsubtitles', 'true') == 'true'
    # Separate subtitle url for hls-streams
    if subtitles_visible and stream.subtitle_url is not None:
        log(2, 'Subtitle URL: {url}', url=unquote(stream.subtitle_url))
        play_item.setSubtitles([stream.subtitle_url])

    log(1, 'Play: {url}', url=unquote(stream.stream_url))
    xbmcplugin.setResolvedUrl(plugin.handle, bool(stream.stream_url), listitem=play_item)

    while not xbmc.Player().isPlaying() and not xbmc.Monitor().abortRequested():
        xbmc.sleep(100)
    xbmc.Player().showSubtitles(subtitles_visible)


def get_search_string():
    ''' Ask the user for a search string '''
    search_string = None
    keyboard = xbmc.Keyboard('', localize(30134))
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_string = to_unicode(keyboard.getText())
    return search_string


def ok_dialog(heading='', message=''):
    ''' Show Kodi's OK dialog '''
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    return Dialog().ok(heading=heading, line1=message)


def notification(heading='', message='', icon='info', time=4000):
    ''' Show a Kodi notification '''
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    if not icon:
        icon = addon_icon()
    Dialog().notification(heading=heading, message=message, icon=icon, time=time)


def multiselect(heading='', options=None, autoclose=0, preselect=None, use_details=False):
    ''' Show a Kodi multi-select dialog '''
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    return Dialog().multiselect(heading=heading, options=options, autoclose=autoclose, preselect=preselect, useDetails=use_details)


def set_locale():
    ''' Load the proper locale for date strings, only once '''
    if hasattr(set_locale, 'cached'):
        return getattr(set_locale, 'cached')
    from locale import LC_ALL, setlocale
    locale_lang = get_global_setting('locale.language').split('.')[-1]
    try:
        # NOTE: This only works if the platform supports the Kodi configured locale
        setlocale(LC_ALL, locale_lang)
    except Exception as exc:  # pylint: disable=broad-except
        if locale_lang != 'en_gb':
            log(3, "Your system does not support locale '{locale}': {error}", locale=locale_lang, error=exc)
            set_locale.cached = False
            return False
    set_locale.cached = True
    return True


def localize(string_id, **kwargs):
    ''' Return the translated string from the .po language files, optionally translating variables '''
    from xbmcaddon import Addon
    if kwargs:
        from string import Formatter
        return Formatter().vformat(Addon().getLocalizedString(string_id), (), SafeDict(**kwargs))

    return Addon().getLocalizedString(string_id)


def localize_date(date, strftime):
    ''' Return a localized date, even if the system does not support your locale '''
    has_locale = set_locale()
    # When locale is supported, return original format
    if has_locale:
        return date.strftime(strftime)
    # When locale is unsupported, translate weekday and month
    if '%A' in strftime:
        strftime = strftime.replace('%A', WEEKDAY_LONG[date.strftime('%w')])
    elif '%a' in strftime:
        strftime = strftime.replace('%a', WEEKDAY_SHORT[date.strftime('%w')])
    if '%B' in strftime:
        strftime = strftime.replace('%B', MONTH_LONG[date.strftime('%m')])
    elif '%b' in strftime:
        strftime = strftime.replace('%b', MONTH_SHORT[date.strftime('%m')])
    return date.strftime(strftime)


def localize_datelong(date):
    ''' Return a localized long date string '''
    return localize_date(date, xbmc.getRegion('datelong'))


def localize_from_data(name, data):
    ''' Return a localized name string from a Dutch data object '''
    # Return if Kodi language is Dutch
    if get_global_setting('locale.language') == 'resource.language.nl_nl':
        return name
    return next((localize(item.get('msgctxt')) for item in data if item.get('name') == name), name)


def get_setting(key, default=None):
    ''' Get an add-on setting '''
    from xbmcaddon import Addon
    value = to_unicode(Addon().getSetting(key))
    if value == '' and default is not None:
        return default
    return value


def set_setting(key, value):
    ''' Set an add-on setting '''
    from xbmcaddon import Addon
    return Addon().setSetting(key, from_unicode(str(value)))


def open_settings():
    ''' Open the add-in settings window, shows Credentials '''
    from xbmcaddon import Addon
    Addon().openSettings()


def get_global_setting(key):
    ''' Get a Kodi setting '''
    result = jsonrpc(method='Settings.GetSettingValue', params=dict(setting=key))
    return result.get('result', {}).get('value')


def get_property(key, window_id=10000):
    ''' Get a Window property '''
    from xbmcgui import Window
    return to_unicode(Window(window_id).getProperty(key))


def set_property(key, value, window_id=10000):
    ''' Set a Window property '''
    from xbmcgui import Window
    return Window(window_id).setProperty(key, from_unicode(str(value)))


def clear_property(key, window_id=10000):
    ''' Clear a Window property '''
    from xbmcgui import Window
    return Window(window_id).clearProperty(key)


def notify(sender, message, data):
    ''' Send a notification to Kodi using JSON RPC '''
    result = jsonrpc(method='JSONRPC.NotifyAll', params=dict(
        sender=sender,
        message=message,
        data=data,
    ))
    if result.get('result') != 'OK':
        log_error('Failed to send notification: {error}', error=result.get('error').get('message'))
        return False
    log(2, 'Succesfully sent notification')
    return True


def get_playerid():
    ''' Get current playerid '''
    result = dict()
    while not result.get('result'):
        result = jsonrpc(method='Player.GetActivePlayers')
    return result.get('result', [{}])[0].get('playerid')


def get_max_bandwidth():
    ''' Get the max bandwidth based on Kodi and add-on settings '''
    vrtnu_max_bandwidth = int(get_setting('max_bandwidth', '0'))
    global_max_bandwidth = int(get_global_setting('network.bandwidth'))
    if vrtnu_max_bandwidth != 0 and global_max_bandwidth != 0:
        return min(vrtnu_max_bandwidth, global_max_bandwidth)
    if vrtnu_max_bandwidth != 0:
        return vrtnu_max_bandwidth
    if global_max_bandwidth != 0:
        return global_max_bandwidth
    return 0


def has_socks():
    ''' Test if socks is installed, and use a static variable to remember '''
    if hasattr(has_socks, 'cached'):
        return getattr(has_socks, 'cached')
    try:
        import socks  # noqa: F401; pylint: disable=unused-variable,unused-import
    except ImportError:
        has_socks.cached = False
        return None  # Detect if this is the first run
    has_socks.cached = True
    return True


def get_proxies():
    ''' Return a usable proxies dictionary from Kodi proxy settings '''
    usehttpproxy = get_global_setting('network.usehttpproxy')
    if usehttpproxy is not True:
        return None

    try:
        httpproxytype = int(get_global_setting('network.httpproxytype'))
    except ValueError:
        httpproxytype = 0

    socks_supported = has_socks()
    if httpproxytype != 0 and not socks_supported:
        # Only open the dialog the first time (to avoid multiple popups)
        if socks_supported is None:
            ok_dialog('', localize(30966))  # Requires PySocks
        return None

    proxy_types = ['http', 'socks4', 'socks4a', 'socks5', 'socks5h']
    if 0 <= httpproxytype < 5:
        httpproxyscheme = proxy_types[httpproxytype]
    else:
        httpproxyscheme = 'http'

    httpproxyserver = get_global_setting('network.httpproxyserver')
    httpproxyport = get_global_setting('network.httpproxyport')
    httpproxyusername = get_global_setting('network.httpproxyusername')
    httpproxypassword = get_global_setting('network.httpproxypassword')

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


def get_cond_visibility(condition):
    ''' Test a condition in XBMC '''
    return xbmc.getCondVisibility(condition)


def has_inputstream_adaptive():
    ''' Whether InputStream Adaptive is installed and enabled in add-on settings '''
    return get_setting('useinputstreamadaptive', 'true') == 'true' and has_addon('inputstream.adaptive')


def has_addon(addon):
    ''' Checks if add-on is installed '''
    return xbmc.getCondVisibility('System.HasAddon(%s)' % addon) == 1


def has_credentials():
    ''' Whether the add-on has credentials filled in '''
    return bool(get_setting('username') and get_setting('password'))


def kodi_version():
    ''' Returns major Kodi version '''
    return int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])


def can_play_drm():
    ''' Whether this Kodi can do DRM using InputStream Adaptive '''
    return get_setting('usedrm', 'true') == 'true' and get_setting('useinputstreamadaptive', 'true') == 'true' and supports_drm()


def supports_drm():
    ''' Whether this Kodi version supports DRM decryption using InputStream Adaptive '''
    return kodi_version() > 17


def get_tokens_path():
    ''' Cache and return the userdata tokens path '''
    if not hasattr(get_tokens_path, 'cached'):
        get_tokens_path.cached = addon_profile() + 'tokens/'
    return getattr(get_tokens_path, 'cached')


def get_cache_path():
    ''' Cache and return the userdata cache path '''
    if not hasattr(get_cache_path, 'cached'):
        get_cache_path.cached = addon_profile() + 'cache/'
    return getattr(get_cache_path, 'cached')


def get_addon_info(key):
    ''' Return addon information '''
    from xbmcaddon import Addon
    return Addon().getAddonInfo(key)


def listdir(path):
    ''' Return all files in a directory (using xbmcvfs)'''
    from xbmcvfs import listdir as vfslistdir
    return vfslistdir(path)


def mkdir(path):
    ''' Create a directory (using xbmcvfs) '''
    from xbmcvfs import mkdir as vfsmkdir
    log(3, "Create directory '{path}'.", path=path)
    return vfsmkdir(path)


def mkdirs(path):
    ''' Create directory including parents (using xbmcvfs) '''
    from xbmcvfs import mkdirs as vfsmkdirs
    log(3, "Recursively create directory '{path}'.", path=path)
    return vfsmkdirs(path)


def exists(path):
    ''' Whether the path exists (using xbmcvfs)'''
    from xbmcvfs import exists as vfsexists
    return vfsexists(path)


@contextmanager
def open_file(path, flags='r'):
    ''' Open a file (using xbmcvfs) '''
    from xbmcvfs import File
    fdesc = File(path, flags)
    yield fdesc
    fdesc.close()


def stat_file(path):
    ''' Return information about a file (using xbmcvfs) '''
    from xbmcvfs import Stat
    return Stat(path)


def delete(path):
    ''' Remove a file (using xbmcvfs) '''
    from xbmcvfs import delete as vfsdelete
    log(3, "Delete file '{path}'.", path=path)
    return vfsdelete(path)


def delete_cached_thumbnail(url):
    ''' Remove a cached thumbnail from Kodi in an attempt to get a realtime live screenshot '''
    # Get texture
    result = jsonrpc(method='Textures.GetTextures', params=dict(
        filter=dict(
            field='url',
            operator='is',
            value=url,
        ),
    ))
    if result.get('result', {}).get('textures') is None:
        log_error('URL {url} not found in texture cache', url=url)
        return False

    texture_id = next((texture.get('textureid') for texture in result.get('result').get('textures')), None)
    if not texture_id:
        log_error('URL {url} not found in texture cache', url=url)
        return False
    log(2, 'found texture_id {id} for url {url} in texture cache', id=texture_id, url=url)

    # Remove texture
    result = jsonrpc(method='Textures.RemoveTexture', params=dict(textureid=texture_id))
    if result.get('result') != 'OK':
        log_error('failed to remove {url} from texture cache: {error}', url=url, error=result.get('error', {}).get('message'))
        return False

    log(2, 'succesfully removed {url} from texture cache', url=url)
    return True


def human_delta(seconds):
    ''' Return a human-readable representation of the TTL '''
    from math import floor
    days = int(floor(seconds / (24 * 60 * 60)))
    seconds = seconds % (24 * 60 * 60)
    hours = int(floor(seconds / (60 * 60)))
    seconds = seconds % (60 * 60)
    if days:
        return '%d day%s and %d hour%s' % (days, 's' if days != 1 else '', hours, 's' if hours != 1 else '')
    minutes = int(floor(seconds / 60))
    seconds = seconds % 60
    if hours:
        return '%d hour%s and %d minute%s' % (hours, 's' if hours != 1 else '', minutes, 's' if minutes != 1 else '')
    if minutes:
        return '%d minute%s and %d second%s' % (minutes, 's' if minutes != 1 else '', seconds, 's' if seconds != 1 else '')
    return '%d second%s' % (seconds, 's' if seconds != 1 else '')


def get_cache(path, ttl=None):
    ''' Get the content from cache, if it's still fresh '''
    if get_setting('usehttpcaching', 'true') == 'false':
        return None

    fullpath = get_cache_path() + path
    if not exists(fullpath):
        return None

    from time import localtime, mktime
    mtime = stat_file(fullpath).st_mtime()
    now = mktime(localtime())
    if ttl is None or now - mtime < ttl:
        from json import load
        if ttl is None:
            log(3, "Cache '{path}' is forced from cache.", path=path)
        else:
            log(3, "Cache '{path}' is fresh, expires in {time}.", path=path, time=human_delta(mtime + ttl - now))
        with open_file(fullpath, 'r') as fdesc:
            try:
                # return load(fdesc, encoding='utf-8')
                return load(fdesc)
            except (TypeError, ValueError):  # No JSON object could be decoded
                return None

    return None


def update_cache(path, data):
    ''' Update the cache, if necessary '''
    if get_setting('usehttpcaching', 'true') == 'false':
        return

    from hashlib import md5
    from json import dump, dumps
    fullpath = get_cache_path() + path
    if exists(fullpath):
        with open_file(fullpath) as fdesc:
            cachefile = fdesc.read().encode('utf-8')
        md5_cache = md5(cachefile)
    else:
        md5_cache = 0
        # Create cache directory if missing
        if not exists(get_cache_path()):
            mkdirs(get_cache_path())

    # Avoid writes if possible (i.e. SD cards)
    if md5_cache != md5(dumps(data).encode('utf-8')):
        log(3, "Write cache '{path}'.", path=path)
        with open_file(fullpath, 'w') as fdesc:
            # dump(data, fdesc, encoding='utf-8')
            dump(data, fdesc)
    else:
        # Update timestamp
        from os import utime
        log(3, "Cache '{path}' has not changed, updating mtime only.", path=path)
        utime(path)


def refresh_caches(cache_file=None):
    ''' Invalidate the needed caches and refresh container '''
    files = ['favorites.json', 'oneoff.json', 'resume_points.json']
    if cache_file and cache_file not in files:
        files.append(cache_file)
    invalidate_caches(*files)
    container_refresh()
    notification(message=localize(30981))


def invalidate_caches(*caches):
    ''' Invalidate multiple cache files '''
    import fnmatch
    _, files = listdir(get_cache_path())
    # Invalidate caches related to menu list refreshes
    removes = set()
    for expr in caches:
        removes.update(fnmatch.filter(files, expr))
    for filename in removes:
        delete(get_cache_path() + filename)


def input_down():
    ''' Move the cursor down '''
    jsonrpc(method='Input.Down')


def current_container_url():
    ''' Get current container plugin:// url '''
    url = xbmc.getInfoLabel('Container.FolderPath')
    if url == '':
        return None
    return url


def container_refresh(url=None):
    ''' Refresh the current container or (re)load a container by URL '''
    if url:
        log(3, 'Execute: Container.Refresh({url})', url=url)
        xbmc.executebuiltin('Container.Refresh({url})'.format(url=url))
    else:
        log(3, 'Execute: Container.Refresh')
        xbmc.executebuiltin('Container.Refresh')


def container_update(url=None):
    ''' Update the current container with respect for the path history. '''
    if url:
        log(3, 'Execute: Container.Update({url})', url=url)
        xbmc.executebuiltin('Container.Update({url})'.format(url=url))
    else:
        # URL is a mandatory argument for Container.Update, use Container.Refresh instead
        container_refresh()


def end_of_directory():
    ''' Close a virtual directory, required to avoid a waiting Kodi '''
    from addon import plugin
    xbmcplugin.endOfDirectory(handle=plugin.handle, succeeded=False, updateListing=False, cacheToDisc=False)


def log(level=1, message='', **kwargs):
    ''' Log info messages to Kodi '''
    debug_logging = get_global_setting('debug.showloginfo')  # Returns a boolean
    max_log_level = int(get_setting('max_log_level', 0))
    if not debug_logging and not (level <= max_log_level and max_log_level != 0):
        return
    if kwargs:
        from string import Formatter
        message = Formatter().vformat(message, (), SafeDict(**kwargs))
    message = '[{addon}] {message}'.format(addon=addon_id(), message=message)
    xbmc.log(from_unicode(message), level % 3 if debug_logging else 2)


def log_access(url, query_string=None):
    ''' Log addon access '''
    message = 'Access: %s' % (url + ('?' + query_string if query_string else ''))
    log(1, message)


def log_error(message, **kwargs):
    ''' Log error messages to Kodi '''
    if kwargs:
        from string import Formatter
        message = Formatter().vformat(message, (), SafeDict(**kwargs))
    message = '[{addon}] {message}'.format(addon=addon_id(), message=message)
    xbmc.log(from_unicode(message), 4)


def jsonrpc(**kwargs):
    ''' Perform JSONRPC calls '''
    from json import dumps, loads
    if 'id' not in kwargs:
        kwargs.update(id=1)
    if 'jsonrpc' not in kwargs:
        kwargs.update(jsonrpc='2.0')
    return loads(xbmc.executeJSONRPC(dumps(kwargs)))