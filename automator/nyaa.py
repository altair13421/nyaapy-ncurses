import requests
from automator import BASE_URL, utils

def search_torrent(*args, **kwargs):
    search = kwargs.get('search', "")
    search = search.replace(' ', '+')
    filter = kwargs.get('filter', 0)
    user = kwargs.get('user', None)
    category = kwargs.get('category', 0)
    sub_category = kwargs.get('sub_category', 0)
    page = kwargs.get('page', 1)

    if user is not None:
        # url = f'{BASE_URL}/user/{user}?f={filter}&c={category}_{sub_category}&q={search}&p={page}'
        url = f'{BASE_URL}/user/{user}?'
        if filter is not None:
            url += f'&f={filter}'
        if search is not None:
            url += f'&q={search}'
        if category is not None and sub_category is not None:
            url += f'&c={category}_{sub_category}'
        if page is not None:
            url += f'&p={page}'
    else:
        # url = f'{BASE_URL}/?f={filter}&c={category}_{sub_category}&q={search}&p={page}&page=rss'
        url = f'{BASE_URL}/?'
        if filter is not None:
            url += f'&f={filter}'
        if search is not None:
            url += f'&q={search}'
        if category is not None and sub_category is not None:
            url += f'&c={category}_{sub_category}'
        if page is not None:
            url += f'&p={page}'
        url += '&page=rss'
    
    url_request = requests.get(url)
    url_request.raise_for_status()
    
    if user is None:
        all_data = utils.parse_rss(url_request.text)
    else:
        all_data = utils.parse_nyaa(url_request.text)
    return all_data
