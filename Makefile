build/geofollow: geofollow.go
	mkdir -p $(@D)
	go build -o $@ $<

build/geofollow.exe: geofollow.go
	mkdir -p $(@D)
	GOOS=windows GOARCH=386 go build -o $@ $<
