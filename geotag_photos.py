#!/usr/bin/env python
import argparse
from typing import Optional
from pathlib import Path
import gpxpy.parser as parser
from gpxpy.gpx import GPXTrackPoint
import pytz
import sys
from datetime import datetime, timedelta
import pyexif  # type: ignore
from dataclasses import dataclass


class GPException(Exception):
    pass


@dataclass
class GPResult:
    date: datetime
    point: Optional[GPXTrackPoint]


class GeotagPhotos:
    def __init__(
        self,
        gpx_path: Path,
        # TODO: defualt timezone None and check gpx timezone
        timezone: str = "UTC",
    ):
        self.timezone = timezone
        with gpx_path.open() as f:
            gpx_parser = parser.GPXParser(f)
            self.gpx = gpx_parser.parse()

        if len(self.gpx.tracks) == 0:
            raise GPException("No tracks in GPX file")
        elif len(self.gpx.tracks[0].segments) == 0:
            raise GPException("No empty track in GPX file")
        elif len(self.gpx.tracks[0].segments[0].points) == 0:
            raise GPException("Invalid track in GPX file")

    def geotag(self, image: Path) -> GPResult:
        photo_date = self._get_photo_date(image)
        point = self._get_coordinates(photo_date)
        return self._write_coordinates(point, image)

    def _get_photo_date(self, photo: Path) -> datetime:
        img = pyexif.ExifEditor(photo)
        datetimeoriginal: str = img.getTag("DateTimeOriginal")
        if datetimeoriginal is not None:
            date = datetime.strptime(datetimeoriginal, "%Y:%m:%d %H:%M:%S").astimezone(
                pytz.timezone(self.timezone)
            )
        else:
            # If there is no DateTimeOriginal, can we try using filesystem's datetime?
            date = datetime.utcfromtimestamp(photo.stat().st_ctime)
        return date

    def _get_coordinates(self, photo_date: datetime) -> Optional[GPXTrackPoint]:
        oldpoint = self.gpx.tracks[0].segments[0].points[0]
        if oldpoint.time is None:
            return None
        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time is None:
                        # TODO: time can be None. Can be None for just one point?
                        #       we just skip points where time is None
                        continue

                    if photo_date > oldpoint.time and photo_date <= point.time:
                        return point

                    oldpoint = point
        return None

    def _write_coordinates(
        self, point: Optional[GPXTrackPoint], photo: Path
    ) -> GPResult:
        date = self._get_photo_date(photo)
        # point.latitude point.longitude point.elevation  point.time
        if point is not None:
            img = pyexif.ExifEditor(photo)
            img.setTag("GPSLatitude", point.latitude)
            img.setTag("GPSLongitude", point.longitude)
            img.setTag("GPSAltitude", point.elevation)
        return GPResult(date, point)


def main():
    parser = argparse.ArgumentParser(
        description="Geotag photos from matching GPX track"
    )
    parser.add_argument(
        "-g", "--gpx", type=Path, required=True, help="File GPX to match photos to"
    )
    parser.add_argument(
        "images", type=Path, metavar="IMAGE", nargs="+", help="Image file to geotag"
    )
    args = parser.parse_args()

    try:
        geotagger = GeotagPhotos(args.gpx)
        for image in args.images:
            r = geotagger.geotag(image)
            if r.point is None:
                print(f"Position not avaiable for {image} at {r.date}")
            else:
                print(
                    f"Photo {image} position: {r.point.latitude}, {r.point.longitude}, {r.point.elevation}"
                )

    except GPException as e:
        sys.exit(e)


if __name__ == "__main__":
    main()
