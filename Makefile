.PHONY: mypy black check

check: mypy black

mypy:
	mypy geotag_photos.py

black:
	black geotag_photos.py