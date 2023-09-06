Script to set geotag to photo from gpx file

## Usage

```
geotag_photos.py [-h] -g GPX [-z TIMEZONE] IMAGE [IMAGE ...]

positional arguments:
  IMAGE                 Image file to geotag

options:
  -h, --help            show this help message and exit
  -g GPX, --gpx GPX     File GPX to match photos to
  -z TIMEZONE, --timezone TIMEZONE
                        Force timezone on photos creation datetime. Must be a valid IANA timezone identifier, e.g.
                        'Europe/Paris', or an offset '+02:00'. If not set, timezone from gpx track is used.
```
