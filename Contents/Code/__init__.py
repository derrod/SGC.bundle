# Stargate Command Channel
import certifi
import requests

PREFIX = "/video/sgc"

TITLE = 'Stargate Command'
MAIN_ART = 'art-default.jpg'
MAIN_ICON = 'icon-default.png'
ICON_SHOWS = 'icon-default.png'
ICON_MOVIES = 'icon-default.png'

API_URL = 'https://mgm-cms.top-fan.com/api/v3/%s'

# Placeholder media URL for URL service since we don't want a generic ooyala handler
MEDIAURL = "http://sgc.doesntexist/%s"

# Headers of the App
HTTP_HEADERS = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 8.0.0; Pixel 2 Build/MXXXX)"}

####################################################################################################
def Start():
    Log.Debug('Starting SGC plugin...')
    ObjectContainer.title1 = 'Stargate Command'
    DirectoryItem.thumb = R(MAIN_ICON)
    VideoItem.thumb = R(MAIN_ICON)
    HTTP.CacheTime = 3600.0
    Dict['oauth_token'] = ''

def ApiRequest(path, get_params=None):
    oauth_token = Dict['oauth_token']
    # Get OAuth token if we don't have one
    # Tokens are valid for a month and since we get a new one each launch we don't bother with any 401 handling.
    if not oauth_token:
        response = requests.post(API_URL % 'oauth/token?grant_type=client_credentials&client_id=azGpBT617osnitO5z3XHUJ6MDXU9fDMgorVtsjz9hV4Q5Kv8&client_secret=67nnplFNwaXcXtAiOGhycFSM2C896scKUAtFhwvaAUrJ5GI1&language_code=en_US&country_code=US', headers=HTTP_HEADERS, verify=certifi.where())
        oauth_token = Dict['oauth_token'] = response.json()['access_token']
    
    if not get_params:
        get_params = {}
    full_url = API_URL % path
    get_params['oauth_token'] = oauth_token
    get_params['language_code'] = 'en_US'
    get_params['country_code'] = 'US'
    params = '&'.join('{}={}'.format(k, v) for k, v in get_params.items())
    response = requests.get(full_url + '?' + params, headers=HTTP_HEADERS, verify=certifi.where())
    return response.json()
    
####################################################################################################
@handler(PREFIX, TITLE, MAIN_ICON, MAIN_ART)
def MainMenu():
	oc = ObjectContainer(no_cache = False)
	oc.add(DirectoryObject(
            key = Callback(SeriesIndex),
            title = 'Series',
            thumb = R(ICON_SHOWS),
            summary = 'Series'))
	oc.add(DirectoryObject(
            key = Callback(MoviesIndex),
            title = 'Movies',
            thumb = R(ICON_MOVIES),
            summary = 'Movies'))
	return oc

@route(PREFIX + '/series')
def SeriesIndex():
    oc = ObjectContainer(title2='Series')
    shows = ApiRequest('client/series')['cards']
    for show in shows:
        show = show['content']
        show_id = show['_id']
        oc.add(TVShowObject(
                key=Callback(SeasonsIndex, show_id=show_id, show_name=show['title']),
                rating_key=show_id, title=show['title'],
                thumb = Resource.ContentsOfURLWithFallback(show['carousel_image'])
                ))
    return oc

@route(PREFIX + '/seasons', show_id=str, show_name=str)
def SeasonsIndex(show_id, show_name=''):
    oc = ObjectContainer(title2='Seasons')
    seasons = ApiRequest('client/series/%s' % show_id)['cards']
    for season_num, season in enumerate(seasons, 1):
        season = season['content']
        season_id = season['_id']
        oc.add(SeasonObject(
                key=Callback(EpisodesIndex, season_id=season_id, season_num=season_num, show_name=show_name),
                rating_key=season_id, title=season['title'],
                thumb = Resource.ContentsOfURLWithFallback(season['images']['image']['original_url'])
                ))
    return oc

@route(PREFIX + '/episodes', season_id=str, season_num=int, show_name=str)
def EpisodesIndex(season_id, season_num, show_name=''):
    oc = ObjectContainer(title2='Episodes')
    
    page = 1
    season = ApiRequest('client/seasons/%s/episodes' % season_id, {'page': page})
    episodes = list(season['cards'])
    if 'pagination' in season:
        while 'next' in season['pagination']:
            # For some reason there's a 'next' even when it's the last page but it will have page=0 in the URL
            if 'page=0' in season['pagination']['next']:
                break
            page += 1
            season = ApiRequest('client/seasons/%s/episodes' % season_id, {'page': page})
            episodes.extend(season['cards'])
    
    Log.Debug(' *** Found %d episodes' % len(episodes))
    for ep_num, episode in enumerate(episodes, 1):
        episode = episode['content']
        # Remove leading number from episode
        clean_title = episode['title'].partition(' ')[2]
        oc.add(EpisodeObject(
                url = MEDIAURL % episode['embed_code'],
                title=clean_title, summary=episode['caption'], season=season_num, show=show_name, index=ep_num,
                absolute_index=int(episode['episode_number']), source_title='Stargate Command',
                thumb = Resource.ContentsOfURLWithFallback(episode['images']['image']['original_url'])
                ))
    return oc

@route(PREFIX + '/movies')
def MoviesIndex():
    oc = ObjectContainer(title2='Movies')
    page = 1
    movies = ApiRequest('client/movies')['cards']
    
    for movie in movies:
        movie = movie['content']
        oc.add(MovieObject(
                url = MEDIAURL % movie['embed_code'],
                title=movie['title'], rating_key=movie['embed_code'], summary=movie['caption'],
                source_title='Stargate Command',
                thumb = Resource.ContentsOfURLWithFallback(movie['images']['image']['original_url'])
                ))
    return oc
