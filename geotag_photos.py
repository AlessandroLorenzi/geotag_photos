#!/usr/bin/env python



import gpxpy.parser as parser
import pytz
import getopt
import sys
from datetime import datetime,timedelta
import exifread
import pyexif
# TODO migrate from exifread to pyexif
# !!! yum install perl-Image-ExifTool !!!


def get_gpx(gpx):
    gpx_file = open( gpx, 'r' )

    gpx_parser = parser.GPXParser( gpx_file )
    gpx_parser.parse()

    gpx_file.close()

    gpx = gpx_parser.get_gpx()
    return gpx

def get_photo_date(photo, tdelta = None):
    img = pyexif.ExifEditor(photo)
    photo_date = img.getTag('DateTimeOriginal')
    photo_date = datetime.strptime(str(photo_date), '%Y:%m:%d %H:%M:%S')
    if tdelta != None:
	photo_date = photo_date + timedelta(hours=int(tdelta))
    
    photo_date = photo_date.replace(tzinfo=pytz.UTC)
    return photo_date


def get_coordinates(gpx, photo_date ):
    oldpoint = gpx.tracks[0].segments[0].points[0]
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
		# LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOONG
                if photo_date > oldpoint.time.replace(tzinfo=pytz.timezone("UTC")) and photo_date < point.time.replace(tzinfo=pytz.timezone("UTC")) or photo_date == point.time.replace(tzinfo=pytz.timezone("UTC")):
                    return(point)

                oldpoint = point


def print_help():
	print 'Syntax: %s [-g|--gpx] file.gpx [[-t|--timediff] -02] file1.jpg [file2.jpg ... ] ' % sys.argv[0]
	exit()


def write_coordinates(point, photo):
	img = pyexif.ExifEditor(photo)

        # point.latitude point.longitude point.elevation  point.time 
	if point != None:
		img.setTag('GPSLatitude',point.latitude)
		img.setTag('GPSLongitude',point.longitude)
		img.setTag('GPSAltitude', point.elevation)
	
	




options, remainder = getopt.getopt(sys.argv[1:], 'g:t:h', ['gpx=', 
                                                         'timezone=',
                                                         'help',
                                                         ])


file_gpx = None
tdelta = None
h=0

for opt, arg in options:
    if opt in ('-g', '--gpx'):
        file_gpx = arg
    elif opt in ('-t', '--timezone'):
        tdelta = arg
    elif opt in ('-h', '--help'):
	h=1

if h==1:
	print_help()

if file_gpx == None:
	exit('Syntax error')



if len(remainder) == 0:
	print_help()

gpx = get_gpx(file_gpx)

for image in remainder:
	photo_date = get_photo_date(image,tdelta)
	point = get_coordinates(gpx,photo_date)
	write_coordinates(point, image)
