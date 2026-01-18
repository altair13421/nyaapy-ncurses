import os
BASE_URL = "https://nyaa.si"
__version__ = "0.10.3"

def hex_to_rgb(hex_code):
    return tuple(int(hex_code[i:i+2], 16) for i in (1, 3, 5))

def get_categories():
    categories = {
        "1": {
            "name": "Anime",
            "color": "#001F3F",
            "sub_cats": {
                "1": "Anime Music Video",
                "2": "English-translated",
                "3": "Non-English-translated",
                "4": "Raw"
            }
        },
        "2": {
            "name": "Audio",
            "color": "#2B2B2B",
            "sub_cats": {
                "1": "Lossless",
                "2": "Lossy"
            }
        },
        "3": {
            "name": "Literature",
            "color": "#85144B",
            "sub_cats": {
                "1": "English-translated",
                "2": "Non-English-translated",
                "3": "Raw"
            }
        },
        "4": {
            "name": "Live Action",
            "color": "#FF851B",
            "sub_cats": {
                "1": "English-translated",
                "2": "Idol/Promotional Video",
                "3": "Non-English-translated",
                "4": "Raw"
            }
        },
        "5": {
            "name": "Pictures",
            "color": "#4E4E4E",
            "sub_cats": {
                "1": "Graphics",
                "2": "Photos"
            }
        },
        "6": {
            "name": "Software",
            "color": "#FF4136",
            "sub_cats": {
                "1": "Applications",
                "2": "Games"
            }
        }
    }
    return categories
