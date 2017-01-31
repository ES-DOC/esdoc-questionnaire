
# pre-defined string lengths...
TINY_STRING = 64
LIL_STRING = 128
SMALL_STRING = 256
BIG_STRING = 512
HUGE_STRING = 1024

CARDINALITY_MIN_CHOICES = [(str(i), str(i)) for i in range(0, 11)]
CARDINALITY_MAX_CHOICES = [('N', 'N')] + [(str(i), str(i)) for i in range(0, 11)]


# minimum password length...
MIN_PASSWORD_LENGTH = 6

# just use the default cache; don't get fancy...
CACHE_ALIAS = "default"

# valid reasons to leave a property value blank (taken from seeGrid)...

NIL_PREFIX = "nil"
NIL_REASONS = [
    ("Unknown", "The correct value is not known, and not computable by, the sender of this data.  However, a correct value probably exists."),
    ("Missing", "The correct value is not readily available to the sender of this data. Furthermore, a correct value may not exist."),
    ("Inapplicable", "There is no value."),
    ("Template", "The value will be available later."),
    ("Withheld", "The value is not divulged."),
]

# naughty words...
# (these are stored in an external file and loaded at startup in "apps.py")
PROFANITIES_LIST = []

# cannot have projects w/ these names...
# (else the URLs won't make sense)
RESERVED_WORDS = [
    "admin", "static", "site_media",
    "user", "login", "logout", "register",
    "questionnaire", "legacy", "metadata", "mindmaps",
    "customize", "edit", "view", "help",
    "api", "services",
    "test", "bak",
]
