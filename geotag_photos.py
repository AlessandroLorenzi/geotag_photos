#!/usr/bin/env python
import argparse
from typing import Optional
from pathlib import Path
import gpxpy.parser as gpxparser
from gpxpy.gpx import GPXTrackPoint
from zoneinfo import ZoneInfo
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
        timezone: Optional[str] = None,
    ):
        with gpx_path.open() as f:
            gpx_parser = gpxparser.GPXParser(f)
            self.gpx = gpx_parser.parse()

        if len(self.gpx.tracks) == 0:
            raise GPException("No tracks in GPX file")
        elif len(self.gpx.tracks[0].segments) == 0:
            raise GPException("No empty track in GPX file")
        elif len(self.gpx.tracks[0].segments[0].points) == 0:
            raise GPException("Invalid track in GPX file")

        if timezone is None:
            # get timezone from first gpx point time
            point = self.gpx.tracks[0].segments[0].points[0]
            if point.time is None:
                # No time... fallback to system tz
                # getting system timezone in python seems to be quite an adventure
                self.tzinfo = datetime.now(ZoneInfo("UTC")).astimezone().tzinfo
            else:
                self.tzinfo = point.time.tzinfo
        else:
            if timezone[0] in ("+", "-") and ":" in timezone:
                self.tzinfo = datetime.strptime(timezone, "%z").tzinfo
            else:
                self.tzinfo = ZoneInfo(timezone)

    def geotag(self, image: Path) -> GPResult:
        photo_date = self._get_photo_date(image)
        point = self._get_coordinates(photo_date)
        return self._write_coordinates(point, image)

    def _get_photo_date(self, photo: Path) -> datetime:
        img = pyexif.ExifEditor(photo)
        datetimeoriginal: str = img.getTag("DateTimeOriginal")
        if datetimeoriginal is not None:
            date = datetime.strptime(datetimeoriginal, "%Y:%m:%d %H:%M:%S").replace(
                tzinfo=self.tzinfo
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
        "-z",
        "--timezone",
        type=str,
        help="Force timezone on photos creation datetime. Must be a valid IANA timezone identifier, e.g. 'Europe/Paris', or an offset '+02:00'. If not set, timezone from gpx track is used.",
    )
    parser.add_argument(
        "images", type=Path, metavar="IMAGE", nargs="+", help="Image file to geotag"
    )
    args = parser.parse_args()

    try:
        geotagger = GeotagPhotos(args.gpx, args.timezone)
        for image in args.images:
            r = geotagger.geotag(image)
            if r.point is None:
                print(f"Position not avaiable for {image} at {r.date}")
            else:
                print(
                    f"Photo {image} at {r.date} position: {r.point.latitude}, {r.point.longitude}, {r.point.elevation}"
                )

    except Exception as e:
        sys.exit(e)


if __name__ == "__main__":
    main()
