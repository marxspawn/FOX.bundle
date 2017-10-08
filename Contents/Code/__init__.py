PREFIX = '/video/fox'
TITLE = 'FOX'
ART = 'art-default.jpg'
ICON = 'icon-default.jpg'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38'

SHOWS_PANELS = 'https://api.fox.com/fbc-content/v1_4/screenpanels/57d15aaa3721cfe22013ead4/items?itemsPerPage=100&page=1'

####################################################################################################
def Start():

	ObjectContainer.title1 = TITLE
	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()
	json_obj = GetJSON(SHOWS_PANELS)

	for member in json_obj['member']:

		if member['seriesType'] != 'series' or member['fullEpisodeCount'] < 1:
			continue

		url = member['screenUrl']
		title = member['name']
		thumb = member['images']['seriesList']['FHD']

		oc.add(DirectoryObject(
			key = Callback(Series, url=url, show=title),
			title = title,
			thumb = thumb
		))

	oc.objects.sort(key=lambda obj: Regex('^The ').split(obj.title)[-1])
	return oc

####################################################################################################
@route(PREFIX + '/series')
def Series(url, show):

	oc = ObjectContainer(title2=show)
	json_obj = GetJSON(url)

	for member in json_obj['panels']['member']:

		if member['panelType'] != 'seriesCollection':
			continue

		for item in member['items']['member']:

			if item['@type'] != 'Season' or item['fullEpisodeCount'] < 1:
				continue

			requires_auth = True
			url = item['episodes']['@id']

			json_obj = GetJSON(url)

			for member in json_obj['member']:

				if member['requiresAuth'] == False:
					requires_auth = False
					break

			if requires_auth:
				continue

			title = 'Season %s' % (item['seasonNumber'])
			thumb = item['autoPlayStill']['default']['url']

			oc.add(DirectoryObject(
				key = Callback(Episodes, url=url, title=title),
				title = title,
				thumb = thumb
			))

	if len(oc) < 1:
		Log(" --- There aren't any free episodes available for %s ---" % (show))
		return ObjectContainer(header="No episodes available for show", message="There aren't any free episodes available for this show")
	else:
		return oc

####################################################################################################
@route(PREFIX + '/episodes')
def Episodes(url, title):

	oc = ObjectContainer(title2=title)
	json_obj = GetJSON(url)

	for member in json_obj['member']:

		if member['requiresAuth']:
			continue

		url = 'https://www.fox.com/watch/%s/' % (member['id'])
		show = member['seriesName']
		title = member['name']
		summary = member['description']
		thumb = member['images']['still']['FHD']
		duration = member['durationInSeconds'] * 1000
		season = int(member['seasonNumber']) if member['seasonNumber'] is not None else None
		index = int(member['episodeNumber']) if member['episodeNumber'] is not None else None
		originally_available_at = Datetime.ParseDate(member['originalAirDate'])

		oc.add(EpisodeObject(
			url = url,
			show = show,
			title = title,
			summary = summary,
			thumb = thumb,
			duration = duration,
			season = season,
			index = index,
			originally_available_at = originally_available_at
		))

	return oc

####################################################################################################
@route(PREFIX + '/api/json')
def GetJSON(url):

	json_obj = JSON.ObjectFromURL(url, headers={"User-Agent": USER_AGENT, "apikey": "abdcbed02c124d393b39e818a4312055"})
	return json_obj
