#!/usr/bin/env python

import gpxpy.parser as parser
import pytz
import getopt
import sys
from datetime import datetime, timedelta
import pyexif
import os


class GeotagPhotos:
    def __init__(
        self,
        gpx_path: str,
        images: list[str],
        # TODO: defualt timezone None and check gpx timezone
        timezone: str = "UTC",
    ):
        self.gpx_path = gpx_path
        self.images = images
        self.timezone = timezone

    def __call__(self):
        self.get_gpx()
        for image in self.images:
            photo_date = self.get_photo_date(image)
            point = self.get_coordinates(photo_date)
            self.write_coordinates(point, image)

    def get_gpx(self):
        gpx_file = open(self.gpx_path, "r")

        gpx_parser = parser.GPXParser(gpx_file)
        self.gpx = gpx_parser.parse()

        gpx_file.close()

    def get_photo_date(self, photo):
        img = pyexif.ExifEditor(photo)
        date = datetime.strptime(
            str(img.getTag("DateTimeOriginal")), "%Y:%m:%d %H:%M:%S"
        ).astimezone(pytz.timezone(self.timezone))
        return date

    def get_coordinates(self, photo_date):
        oldpoint = self.gpx.tracks[0].segments[0].points[0]
        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if (
                        photo_date > oldpoint.time
                        and photo_date < point.time
                        or photo_date == point.time
                    ):
                        return point

                    oldpoint = point

    def write_coordinates(self, point, photo):
        img = pyexif.ExifEditor(photo)

        # point.latitude point.longitude point.elevation  point.time
        if point is not None:
            img.setTag("GPSLatitude", point.latitude)
            img.setTag("GPSLongitude", point.longitude)
            img.setTag("GPSAltitude", point.elevation)
            print(
                "Photo %s position: %s, %s, %s"
                % (photo, point.latitude, point.longitude, point.elevation)
            )
        else:
            date = self.get_photo_date(photo)
            print("Position not avaiable for %s at %s" % (photo, date))


if __name__ == "__main__":

    def print_help():
        print(
            "Syntax: %s [-g|--gpx] file.gpx [[-t|--timediff] -02] file1.jpg [file2.jpg ... ] "
            % sys.argv[0]
        )
        exit()

    def sanitize_gpx(file_gpx):
        if not os.access(file_gpx, os.R_OK):
            print("File GPX not readable")
            exit()

    options, images = getopt.getopt(
        sys.argv[1:],
        "g:t:h",
        [
            "gpx=",
            "timezone=",
            "help",
        ],
    )

    file_gpx = None
    # TODO: make timezone optional
    timezone = "UTC"
    h = 0

    for opt, arg in options:
        if opt in ("-g", "--gpx"):
            file_gpx = arg
        elif opt in ("-t", "--timezone"):
            timezone = arg
        elif opt in ("-h", "--help"):
            h = 1

    if h == 1:
        print_help()

    if len(images) == 0:
        print_help()

    GeotagPhotos(file_gpx, images, timezone)()
