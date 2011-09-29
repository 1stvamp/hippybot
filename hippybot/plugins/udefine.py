import requests
from BeautifulSoup import BeautifulSoup as Soup
from hippybot.hipchat import HipChatApi
from hippybot.decorators import directcmd

UD_SEARCH_URI = "http://www.urbandictionary.com/iphone/search/define"

class Plugin(object):
    """Plugin to lookup definitions from urbandictionary.com
    """
    global_commands = ('udefine',)

    @directcmd
    def udefine(self, mess, args):
        json = requests.get(UD_SEARCH_URI, params={'term': args})
        results = []
        if json:
            json = json.replace(r'\r', '')
            data = loads(json)
            if data.get('result_type', '') != 'no_results' and \
               data.has_key('list') and len(data['list']) > 0:
                for datum in data['list']:
                    if datum.get('word', '') == term:
                        # Sanitization
                        definition = datum['definition']
                        re.sub(r'\s', ' ', definition)
                        definition = u''.join(Soup(definition).findAll(text=True))
                        definition = unicode(Soup(definition, convertEntities=Soup.HTML_ENTITIES))
                        results.append(definition)
        if results:
            reply = u"\n".join(results)
            return reply
        else:
            return u'No matches found for "%s"' % (args,)

