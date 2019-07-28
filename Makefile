REVNUM = $(shell git describe --always --dirty)
PLUGIN_NAME = GeoFollow
PLUGIN_FILES = \
	metadata.txt \
	icon.png \
	__init__.py \
	geofollow.py \
	geofollow_dialog.py \
	geofollow_dialog_base.ui \
	resources.py

build/geofollow: geofollow.go
	mkdir -p $(@D)
	go build -o $@ $<

build/geofollow.exe: geofollow.go
	mkdir -p $(@D)
	GOOS=windows GOARCH=386 go build -o $@ $<

build/qgis/$(PLUGIN_NAME)/resources.py: qgis/resources.qrc qgis/icon_connect.png qgis/icon_disconnect.png
	mkdir -p $(@D)
	pyrcc4 -o $@  $<

build/qgis/$(PLUGIN_NAME)/%: qgis/%
	mkdir -p $(@D)
	cp $< $@

build/$(PLUGIN_NAME)-qgis-$(REVNUM).zip: $(addprefix build/qgis/$(PLUGIN_NAME)/, $(PLUGIN_FILES))
	cd build/qgis && zip -9r $(@F) $(PLUGIN_NAME)/

zip: build/$(PLUGIN_NAME)-qgis-$(REVNUM).zip
	@echo "Zip ready : $<"

install: $(addprefix build/qgis/$(PLUGIN_NAME)/, $(PLUGIN_FILES))
	cp -va build/qgis/$(PLUGIN_NAME) ~/.qgis2/python/plugins/

clean:
	rm -rf build

.PHONY: clean zip install
