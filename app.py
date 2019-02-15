from flask import Flask, request

import time
import json
import re
import os
import logging

from bs4 import BeautifulSoup
import urllib.request


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class OpenGraph(dict):
    """
    """

    required_attrs = ['title', 'type', 'image', 'url', 'description']

    def __init__(self, url=None, html=None, scrape=False, **kwargs):
        # If scrape == True, then will try to fetch missing attribtues
        # from the page's body

        # self.scrape = scrape
        # self._url = url

        for k in kwargs.keys():
            self[k] = kwargs[k]

        dict.__init__(self)

        if url is not None:
            self.fetch(url)

        if html is not None:
            self.parser(html)

    def __setattr__(self, name, val):
        self[name] = val

    def __getattr__(self, name):
        return self[name]

    def fetch(self, url):
        """
        """
        raw = urllib.request.urlopen(url)
        html = raw.read()
        return self.parser(html)

    def parser(self, html):
        """
        """
        if not isinstance(html,BeautifulSoup):
            doc = BeautifulSoup(html, "html.parser")
        else:
            doc = html
        ogs = doc.html.head.findAll(property=re.compile(r'^og'))
        for og in ogs:
            if og.has_attr(u'content'):
                self[og[u'property'][3:]]=og[u'content']
        # Couldn't fetch all attrs from og tags, try scraping body
        if not self.is_valid() and self.scrape:
            for attr in self.required_attrs:
                if not self.valid_attr(attr):
                    try:
                        self[attr] = getattr(self, 'scrape_%s' % attr)(doc)
                    except AttributeError:
                        pass

    def valid_attr(self, attr):
        return self.get(attr) and len(self[attr]) > 0

    def is_valid(self):
        return all([self.valid_attr(attr) for attr in self.required_attrs])

    def to_html(self):
        if not self.is_valid():
            return u"<meta property=\"og:error\" content=\"og metadata is not valid\" />"

        meta = u""
        for key,value in self.iteritems():
            meta += u"\n<meta property=\"og:%s\" content=\"%s\" />" %(key, value)
        meta += u"\n"

        return meta

    def to_json(self):
        if not self.is_valid():
            return {'error':'og metadata is not valid'}

        return self

    def scrape_image(self, doc):
        images = [dict(img.attrs)['src']
            for img in doc.html.body.findAll('img')]

        if images:
            return images[0]

        return u''

    def scrape_title(self, doc):
        return doc.html.head.title.text

    def scrape_type(self, doc):
        return 'other'

    def scrape_url(self, doc):
        return self._url

    def scrape_description(self, doc):
        tag = doc.html.head.findAll('meta', attrs={"name":"description"})
        result = "".join([t['content'] for t in tag])
        return result

app = Flask(__name__)


@app.route('/', methods=['GET'])
def HOME():
    return_json = {}
    return_json['success'] = False
    return_json['error'] = 'send request to /info/{url}'
    return_json['GETArgs'] = 'scrape={og|html|both}'
    return json.dumps(return_json)


@app.route('/<path:url>', methods=['GET'])
def incoming(url):
    parse = request.args.get('parse')
    if parse == None: parse = 'both'
    return parse_url(url, parse)

def parse_url(url="https://github.com/wannamit", parse='both'):
    return_json = {}
    if url == '':
        return_json['success'] = False
        return json.dumps(return_json)

    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
    headers = {'User-Agent': user_agent}
    
    try:
        req = urllib.request.Request(url, None, headers)
        response = urllib.request.urlopen(req)
        html_page = response.read()
        soup_page = BeautifulSoup(html_page, "html.parser")

        if parse == 'both' or parse == 'og':
            og_scrape = OpenGraph(html=soup_page)
            return_json['og'] = og_scrape.to_json()

        if parse == 'both' or parse == 'html':
            html_scrape = {}
            html_scrape['url'] = url
            
            title = soup_page.find('title')
            if title != None:
                html_scrape['title'] = title.get_text()
            else:
                html_scrape['title'] = url
            
            description_meta = soup_page.find('meta', {'name': 'description'})
            if description_meta != None:
                html_scrape['description'] = description_meta['content']
            else:
                html_scrape['description'] = ''
            return_json['html'] = html_scrape

        return_json['success'] = True
    except Exception as e:
        return_json['success'] = False
        logger.debug('Error fetching data from ' + url, e)

    return json.dumps(return_json)

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", "8088")), debug=False)
