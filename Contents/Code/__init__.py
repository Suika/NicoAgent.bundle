NICO_VIDEO_DETAILS = 'https://www.nicovideo.jp/watch/%s'
RE_NICO_ID = Regex('sm[0-9]+', Regex.IGNORECASE)
import re
import time
import json
from HTMLParser import HTMLParser

def Start():
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'
	
class NicoAgent(Agent.Movies):
    name = 'NicoVideo'
    languages = [Locale.Language.NoLanguage]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']

    def Log(self, message, *args):
        if Prefs['debug']:
            Log(message, *args)

    def search(self, results, media, lang):
        filename = String.Unquote(media.filename)
        try:
            nico_id = Regex('(?P<id>sm[0-9]+)\.').search(filename.split('-')[-1]).group('id')
        except:
            Log('Regex failed: Filename: %s' % filename)
            nico_id = None

        if nico_id and RE_NICO_ID.search(nico_id):
            results.Append(
                MetadataSearchResult(
                    id = nico_id,
                    name = media.name,
                    year = None,
                    score = 99,
                    lang = lang
                )
            )

    def update(self, metadata, media, lang, force=True):
        url = NICO_VIDEO_DETAILS % metadata.id
        htp = HTMLParser()

        try:
            Log(url)
            htmlSource = HTML.ElementFromURL(url)
        except:
            Log('Could not retrieve data from Iwara for: %s' % metadata.id)
            htmlSource = None
            exit(1)
        try:
            jsTree = json.loads(htp.unescape(htp.unescape(htmlSource.xpath('//div[@id="js-initial-watch-data"]/@data-api-data')[0])))
        except:
            exit(1)
        try:
            metadata.title = jsTree["video"]["originalTitle"]
        except:
            pass

        try:
            genres = jsTree["tags"]
            for genre in genres: metadata.genres.add(genre["name"].strip())
        except:
            pass
        try:
            thumb = jsTree["video"]["largeThumbnailURL"]
            metadata.posters[thumb] = Proxy.Preview(HTTP.Request(thumb).content, sort_order=1)
        except:
            pass

        try:
            metadata.summary = jsTree["video"]["originalDescription"]
        except:
            pass
        try:
            date = Datetime.ParseDate(jsTree["video"]["postedDateTime"])
            metadata.originally_available_at = date.date()
            metadata.year = date.year
        except:
            pass

        try:
            if jsTree["video"]["isAdult"]:
                metadata.content_rating = "R"
            elif jsTree["video"]["isR18"]:
                metadata.content_rating = "NC-17"
            else:
                metadata.content_rating = "Unrated"
        except:
            pass
        
        # Add YouTube user as director
        metadata.directors.clear()

        if Prefs['add_user_as_director']:
            try:
                meta_director = metadata.directors.new()
                meta_director.name = jsTree["owner"]["nickname"]
                meta_director.photo = jsTree["owner"]["iconURL"]
            except:
                pass

