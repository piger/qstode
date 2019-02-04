# QStode default configuration


# Available translations
SUPPORTED_LANGUAGES = [("en", "English"), ("it", "Italiano")]

SUPPORTED_LANGUAGES_ISO = [l[0] for l in SUPPORTED_LANGUAGES]

# Number of Bookmarks returned on every page
PER_PAGE = 10

# Number of Bookmarks returned in the RSS feed
FEED_NUM_ENTRIES = 15

# Number of tags listed in the Popular Tags list
TAGLIST_ITEMS = 30

# Temporary switch for related tags
ENABLE_RELATED_TAGS = True

# Enable new users registration
ENABLE_USER_REGISTRATION = True

# Use recaptcha
ENABLE_RECAPTCHA = False

# Autocomplete API: number of tag returned
TAG_AUTOCOMPLETE_MAX = 15

# Restrict registration to the following domains: (empty list disable this feature)
FRIEND_DOMAINS = []
