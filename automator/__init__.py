import os
BASE_URL = "https://nyaa.si"
BASE_SUKEBEI = "https://sukebei.nyaa.si"
__version__ = "0.10.3"

SUB_CATEGORY_COLORS = {
    "1": "#56B4E9",
    "2": "#8CCF7E",
    "3": "#C792EA",
    "4": "#AAB4C3",
}


def hex_to_rgb(hex_code):
    return tuple(int(hex_code[i:i+2], 16) for i in (1, 3, 5))

def get_categories():
    categories = {
        "1": {
            "name": "Anime",
            "color": "#5DADE2",
            "sub_cats": {
                "1": "Anime Music Video",
                "2": "English-translated",
                "3": "Non-English-translated",
                "4": "Raw"
            }
        },
        "2": {
            "name": "Audio",
            "color": "#58D68D",
            "sub_cats": {
                "1": "Lossless",
                "2": "Lossy"
            }
        },
        "3": {
            "name": "Literature",
            "color": "#AF7AC5",
            "sub_cats": {
                "1": "English-translated",
                "2": "Non-English-translated",
                "3": "Raw"
            }
        },
        "4": {
            "name": "Live Action",
            "color": "#F5B041",
            "sub_cats": {
                "1": "English-translated",
                "2": "Idol/Promotional Video",
                "3": "Non-English-translated",
                "4": "Raw"
            }
        },
        "5": {
            "name": "Pictures",
            "color": "#EC7063",
            "sub_cats": {
                "1": "Graphics",
                "2": "Photos"
            }
        },
        "6": {
            "name": "Software",
            "color": "#F4D03F",
            "sub_cats": {
                "1": "Applications",
                "2": "Games"
            }
        }
    }
    return categories
