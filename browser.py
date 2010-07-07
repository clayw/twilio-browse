import web
import urllib
import twilio
import re
import commands

from xml.sax.saxutils import escape

urls = (
    '/voice', 'voice',
    '/voice/(.*)', 'voice',
    '/sms', 'sms_url_input',
    '/', 'web2phone',
)
app = web.application(urls, globals())

API_VERSION = '2008-08-01'
CALLER_ID = ''

TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''

class web2phone:
    def GET(self):
        return '<form action="." method="POST"><table><tr><td>Phone number:</td><td><input type="textbox" name="recp" /></td></tr><tr><td>Url to nagivate to</td><td><input type="textbox" name="url" /></td></tr></table><input type="submit" name="Call" />'
    def POST(self): 
        i = web.input()
        call_initiator(recp=i.recp, url=i.url)
        return '<html>calling %s to navigate to %s <br/>' % (i.recp, i.url)  + self.GET()

class sms_url_input:
    def GET(self):
        # call from number and then run call_initiator
        i = web.input(From=None, Body=None)
        call_initiator(recp=i.From, url = i.Body)
        web.header('Content-Type', 'text/xml')
        return '<?xml version="1.0"?><Response></Response>'

    def POST(self):
        return self.GET()

class voice:
    def GET(self, *args): 
        self.POST(*args)

    def POST(self, url='http://news.ycombinator.com'):
        i = web.input(Digits=None)
        web.header('content-type', 'text/xml')
        return url_dictator(url=url, digits=i.Digits)

def call_initiator(recp, url):
    account = twilio.Account(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    d = {'Caller': CALLER_ID, 
         'Called': recp, 
         'Url': 'http://localhost/voice/%s/' % (urllib.quote(strip_http(url))),}
    try:
        response = account.request('/%s/Accounts/%s/Calls' \
                % (API_VERSION, TWILIO_ACCOUNT_SID), 'POST', d)
        print response
    except Exception, e:
        print e

def url_dictator(url, digits=None):
    """ TODO: caching mechanism """
    if digits:
        f_text, f_links = url_renderer(url=url)
        text, links = url_renderer(url=f_links[digits])
        url = f_links[digits]
    else:
        text, links = url_renderer(url=url)
    text = 'Reading %s, press the link number to navigate to that page %s' % (url, text)
    return '<?xml version="1.0"?><Response><Gather action="/twilio/voice/%s/" method="GET"><Say>%s</Say></Gather></Response>' % (urllib.quote(url), text)

def url_renderer(url):
    resp, text = commands.getstatusoutput('lynx --dump %s' % (urllib.unquote(add_http(url))))
    try:
        voice_text, link_text = text.split('\n\nReferences\n\n')
    except:
        voice_text = text
    links = {}
    for line in link_text.splitlines():
        m = re.match('^\W+(\d+)\. (.*)', line)
        if m:
            number = m.group(1)
            url = m.group(2)
            links[number] = urllib.quote(url)
    return unicode(escape(voice_text), errors='replace'), links

def add_http(url):
    if url[:4] != 'http':
        return 'http://' + url
    else:
        return url

def strip_http(url):
    if url[:7] == 'http://':
        return url[7:]
    else:
        return url

if __name__ == "__main__":
    app.run()
