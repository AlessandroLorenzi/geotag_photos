#!/usr/bin/env python



import gpxpy.parser as parser
import pytz
import getopt
import sys
from datetime import datetime,timedelta
import exifread
import pyexif
import os
# !!! yum install perl-Image-ExifTool !!!

class geotag_photos:
	def __init__(self, file_gpx, image, tdelta):

		gpx = self.get_gpx(file_gpx)
		photo_date = self.get_photo_date(image,tdelta)
		point = self.get_coordinates(gpx,photo_date)
		self.write_coordinates(point, image)


	def get_gpx(self, gpx):
		gpx_file = open( gpx, 'r' )

		gpx_parser = parser.GPXParser( gpx_file )
		gpx_parser.parse()

		gpx_file.close()

		gpx = gpx_parser.get_gpx()
		return gpx

	def get_photo_date(self, photo, tdelta = None):
		img = pyexif.ExifEditor(photo)
		photo_date = img.getTag('DateTimeOriginal')
		photo_date = datetime.strptime(str(photo_date), '%Y:%m:%d %H:%M:%S')
		if tdelta != None:
			photo_date = photo_date + timedelta(hours=int(tdelta))
    
		photo_date = photo_date.replace(tzinfo=pytz.UTC)
		return photo_date


	def get_coordinates(self, gpx, photo_date ):
		oldpoint = gpx.tracks[0].segments[0].points[0]
		for track in gpx.tracks:
			for segment in track.segments:
				for point in segment.points:
					# LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOONG
					if photo_date > oldpoint.time.replace(tzinfo=pytz.timezone("UTC")) and photo_date < point.time.replace(tzinfo=pytz.timezone("UTC")) or photo_date == point.time.replace(tzinfo=pytz.timezone("UTC")):
						return(point)

					oldpoint = point




	def write_coordinates(self, point, photo):
		img = pyexif.ExifEditor(photo)

	        # point.latitude point.longitude point.elevation  point.time 
		if point != None:
			img.setTag('GPSLatitude',point.latitude)
			img.setTag('GPSLongitude',point.longitude)
			img.setTag('GPSAltitude', point.elevation)
			print ('Photo %s position: %s, %s, %s' %(photo, point.latitude , point.longitude, point.elevation))
		else:
			print ('Position not avaiable for %s' % (photo))
	
	
	


if __name__ == "__main__":
	def print_help():
		print 'Syntax: %s [-g|--gpx] file.gpx [[-t|--timediff] -02] file1.jpg [file2.jpg ... ] ' % sys.argv[0]
		exit()

	def sanitize_gpx(file_gpx):
		if not os.access(file_gpx, os.R_OK):
			print('File GPX not readable')
			exit()

	def sanitize_image(image):
		if not os.access(image, os.W_OK):
			print('File image "%s" not writable' % image)
			exit()
		if not os.access(image, os.R_OK):
			print('File image "%s" not readable' % image)
			exit()

	def sanitize_tdelta(tdelta):
		try:
			int(tdelta)
		except:
			print('Time delta "%s" non valido' % tdelta)
			exit()


	options, remainder = getopt.getopt(sys.argv[1:], 'g:t:h', ['gpx=', 
                                                         'timezone=',
                                                         'help',
                                                         ])


	file_gpx = None
	tdelta = 0
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
		print_help()
	else:
		sanitize_gpx(file_gpx)
	
	sanitize_tdelta(tdelta)


	if len(remainder) == 0:
		print_help()


	for image in remainder:
		sanitize_image(image)
		geotag_photos(file_gpx, image, tdelta)

