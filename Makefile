VENV = ./venv
PYBABEL = $(VENV)/bin/pybabel
LANGUAGES = it
TRANSLATIONS_DIR = qstode/translations

all: messages.pot $(patsubst %,$(TRANSLATIONS_DIR)/%/LC_MESSAGES,$(LANGUAGES)) compile

messages.pot: $(PYBABEL)
	$(PYBABEL) extract -F babel.cfg -k lazy_gettext -o $@ -c "Translators:" .
	$(PYBABEL) update -i $@ -d $(TRANSLATIONS_DIR)

$(PYBABEL):
	virtualenv $(VENV)
	$(VENV)/bin/python setup.py develop

$(TRANSLATIONS_DIR)/%/LC_MESSAGES: messages.pot
	$(PYBABEL) init -i $^ -d $(TRANSLATIONS_DIR) -l $(patsubst $(TRANSLATIONS_DIR)/%/LC_MESSAGES,%,$@)

compile: $(patsubst %,$(TRANSLATIONS_DIR)/%/LC_MESSAGES/messages.po,$(LANGUAGES)) $(PYBABEL)
	$(PYBABEL) compile --statistics -d $(TRANSLATIONS_DIR)

.PHONY: compile
