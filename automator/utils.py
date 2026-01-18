import os
import time
import urllib
from lxml import etree
from rich.console import Console
from urllib.parse import urlencode

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
console = Console()

# Nyaa Related
# Ok, so I took this From NyaaPy By Juanjo Salvador
def parse_rss(request_text):
    root =  etree.fromstring(request_text)
    torrents = list()
    for item in root.xpath("channel/item"):
        try:
            item_type = "remake" if (item.findtext('nyaa:remake', namespaces=item.nsmap) == "Yes") else "trusted" if (item.findtext('nyaa:trusted', namespaces=item.nsmap) == 'Yes') else "default"
            torrent = {
                "id": item.findtext('guid').split('/')[-1],
                "publish_date": item.findtext('pubDate'),
                "title": item.findtext('title'),
                'torrent_link': item.findtext('link'),
                'view_link': item.findtext('guid'),
                'magnet': get_magnet(item.findtext('nyaa:infoHash', namespaces=item.nsmap), item.findtext('title')),
                "seeders": item.findtext('nyaa:seeders', namespaces=item.nsmap),
                'category': item.findtext('nyaa:category', namespaces=item.nsmap),
                'categoryid': item.findtext('nyaa:categoryId', namespaces=item.nsmap).split('_'),
                'size': item.findtext('nyaa:size', namespaces=item.nsmap),
                'item_type': item_type
            }
            torrents.append(torrent)
        except IndexError:
            print("it passed")
    return torrents

def get_magnet(info_hash, title):
    known_trackers = [
        "http://nyaa.tracker.wf:7777/announce",
        "udp://open.stealth.si:80/announce",
        "udp://tracker.opentrackr.org:1337/announce",
        "udp://exodus.desync.com:6969/announce",
        "udp://tracker.torrent.eu.org:451/announce"
    ]
    magnet_link = f'magnet:?xt=urn:btih:{info_hash}&{urlencode({"dn": title}, quote_via=urllib.parse.quote)}'
    for tracker in known_trackers:
        magnet_link += f'&{urlencode({"tr": tracker})}'
    return magnet_link

def parse_nyaa(request_text):
    request_text = request_text
    torrents = list()
    return torrents

# OTHERS
def rprint_error(string):
    console.log(f'[red] Error:[/red] [light_pink4]{string} [/light_pink4]')
def rprint_log(string):
    console.log(f'[cyan] Progress:[/cyan] [sky_blue1]{string} [sky_blue1]')
def rprint_success(string):
    console.log(f'[green] Success:[/green] [aquamarine1]{string} [/aquamarine1]')
def sleeper(timer):
    time.sleep(timer)
def get_state_strings(label):
    state = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
    return state[label]
