__author__="allyn.treshansky"
__date__ ="$Sep 30, 2013 4:12:23 PM$"

APP_LABEL     = "questionnaire"

__version_info__ = {
    'major': 0.11,
    'minor': 0,
    'patch': 0,
}

def get_version():
    version = ".".join(str(value) for value in __version_info__.values())
    return version

__version__ = get_version()
