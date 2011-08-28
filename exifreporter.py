#!/usr/bin/env python

"""
EXIF reporter 
(part of ExifViewer project - https://github.com/PicciMario/EXIF-Viewer)
Copyright (c) 2011 PicciMario <mario.piccinelli@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Various dependencies
import sys, math, os, hashlib, time, urllib, getopt

# Exif Data Class
# from the ExifViewer project too
from exifviewer import ExifData

# XML manager
# to manage data read from reverse geocoding
from xml.dom import minidom

# Python Imaging Library
# needed to handle images
import PIL, cStringIO
from PIL import ImageDraw

# ReportLab project dependencies
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, Image, PageBreak, Table, TableStyle, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# socket default timeout
import socket
socket.setdefaulttimeout(10)

def usage():
	print("")
	print("PicciMario EXIF reported v. 0.1")
	print("mario.piccinelli@gmail.com")
	print("")
	print("Analyzes a JPG picture and prints a PDF report with informations about")
	print("the file (as told by the filesystem) and about the image itself via its")
	print("EXIF tags. Special care has been thrown in intepreting the GPS data, if")
	print("present the report will contain a map of the location and an approximate")
	print("reverse geocoding of the coordinates into their location name.")
	print("")
	print("Usage:")
	print("exifreporter.py -f filename -o reportname")
	print("")
	print("If a report name is not provided, the tool will use the default: report.pdf.")

filename = ""
reportFileName = ""

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:o:")
except getopt.GetoptError:
	usage()
	sys.exit(0)

for o,a in opts:
	if o == "-h":
		usage()
		sys.exit(0)
	elif o == "-f":
		filename = a
	elif o == "-o":
		reportFileName = a

if (len(filename) == 0):
	usage()
	print("You need to provide a in input file name.\n")
	sys.exit(1)

if (len(reportFileName) == 0):
	defaultReportFileName = "report.pdf"
	print("Didn't provide an output file name. Using default: %s"%defaultReportFileName)
	reportFileName = defaultReportFileName

# check file existence
if (os.path.isfile(filename) == 0):
	usage()
	print("Provided input file does not exist.\n")
	sys.exit(1)	

# init exif data manager

exifData = ExifData()
result = exifData.openFile(filename)

if (result != 0):
	print("Unable to init data file")
	sys.exit(1)

exifs = exifData.getExifs()

# ------- PDF Styles ----------------------------------------------------

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

styles.add(
	ParagraphStyle(
		name='CodeNoIndent',
		fontName='Courier',
		fontSize=8,
		leading=12,
		firstLineIndent=0,
		leftIndent=0,
		spaceBefore=6
	)
)

styles.add(
	ParagraphStyle(
		name='Small',
		fontName='Times-Roman',
		fontSize=8,
		leading=12,
		spaceBefore=6
	)
)

styles.add(
	ParagraphStyle(
		name='Caption',
		fontName='Times-Italic',
		fontSize=8,
		leading=12,
		spaceBefore=6,
		alignment=TA_CENTER
	)
)

tableStyleStandard = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 1),
	('BOTTOMPADDING', (0,0), (-1,-1), 2),
	('LEFTPADDING', (0,0), (-1,-1), 5),
	('RIGHTPADDING', (0,0), (-1,-1), 5),
])

tableStyleSmall = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 0),
	('BOTTOMPADDING', (0,0), (-1,-1), 0),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

tableStyle4col = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('BACKGROUND',(0,0),(0,-1),colors.lightgrey),
	('BACKGROUND',(2,0),(2,-1),colors.lightgrey),
	('TOPPADDING', (0,0), (-1,-1), 0),
	('BOTTOMPADDING', (0,0), (-1,-1), 0),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

tableStyleImg = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 3),
	('BOTTOMPADDING', (0,0), (-1,-1), 3),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

tableStyleGray = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('BACKGROUND',(0,0),(2,0),colors.lightgrey),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 3),
	('BOTTOMPADDING', (0,0), (-1,-1), 3),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

Story = []

# ------- Header Section ----------------------------------------------------

def fileMd5(original_filename):
	try:
		f = file(original_filename ,'rb')
		
		md5 = hashlib.md5()
		while True:
			data = f.read()
			if not data:
				break
			md5.update(data)
		md5String = md5.hexdigest()
		
		f.close()
		return md5String
	except:
		return ""

Story.append(Paragraph("Image analysis report", styles["Title"]))

thumbWidth = 3*inch
thumbHeight = exifData.imageHeight * (float(thumbWidth) / float(exifData.imageWidth))

im = Image(filename, thumbWidth, thumbHeight)

imgData = Table(
	[
		[
			Paragraph("File name:", styles["Small"]),
			Paragraph("%s"%filename, styles["Small"])
		],
		[
			Paragraph("File size:", styles["Small"]),
			Paragraph("%s kB"%(os.path.getsize(filename)/1024), styles["Small"])
		],
		[
			Paragraph("File MD5:", styles["Small"]),
			Paragraph("%s"%fileMd5(filename), styles["Small"])
		],
		[
			Paragraph("Image format", styles["Small"]), 
			Paragraph(exifData.imageFormat, styles["Small"])
		], 
		[
			Paragraph("Image mode", styles["Small"]), 
			Paragraph(exifData.imageMode, styles["Small"])
		],
		[
			Paragraph("Image size", styles["Small"]), 
			Paragraph("%s px"%exifData.imageSize, styles["Small"])
		],	

	],
	colWidths=[70, 234]
)
imgData.setStyle(tableStyleSmall)

t=Table([[im, imgData]], colWidths=[3*inch+6, 310])
t.setStyle(tableStyleImg)
Story.append(t)

Story.append(Spacer(10, 20))

# ------- FileSystem Section ---------------------------------------------

Story.append(Paragraph("FileSystem data", styles['Heading2']))

stats = os.stat(filename)

# otherTags stores data in 2 column format (tag, value)
otherTags = []

# attrs stores a list of attributes to append (if available) to otherTags
# [attribute tag - attribute descr - type]
# type:
#    0 - none (string)
#    1 - time
#    2 - binary

attrs = [
	['st_mode', 'Protection bits', 2],
	['st_ino', 'Inode number', 0],
	['st_dev', 'Device', 0],
	['st_nlink', 'Number of hard links', 0],
	['st_uid', 'UID of the owner', 0],
	['st_gid', 'GID of the owner', 0],
	['st_atime', 'Time of most recent access', 1],
	['st_mtime', 'Time of most recent content modification', 1],
	['st_ctime', 'Time of most recent metadata change (time of creation in Windows systems)', 1],
	['st_blocks', 'Number of blocks allocated', 0],
	['st_blksize', 'Filesystem block size', 0],
	['st_rdev', 'Type of device', 0],
	['st_flags', 'User defined flags for file', 0],
	['st_gen', 'File generation number', 0],
	['st_birthtime', 'Time of file creation', 1],
	['st_rsize', 'Rsize (mac os specific)', 0],
	['st_creator', 'Creator (mac os specific)', 0],
	['st_type', 'Type (mac os specific)', 0],
]

for attr in attrs:
	if (hasattr(stats, attr[0])):
		value = getattr(stats, attr[0])
		
		if (attr[2] == 1):
			value = time.ctime(value)
		elif (attr[2] == 2):
			value = bin(value)

		otherTags.append(
			[
				Paragraph(attr[1], styles["Small"]), 
				Paragraph("%s"%value, styles["Small"])
			]
		)

# osData stores data in 4 column format (tag1, value1, tag2, value2)
osData = []

# takes data from otherTags and append (two by two) to osData
while True:
	if (len(otherTags) >= 2):
		osData.append([otherTags[0][0], otherTags[0][1], otherTags[1][0], otherTags[1][1]])
		otherTags.pop(0)
		otherTags.pop(0)
	elif (len(otherTags) == 1):
		osData.append([otherTags[0][0], otherTags[0][1], "", ""])
		otherTags.pop(0)
	else:
		break

osDataTable = Table(osData, colWidths=[140, 125, 140, 125])
osDataTable.setStyle(tableStyle4col)
Story.append(osDataTable)

Story.append(Spacer(10, 10))

# ------- MAP Section ----------------------------------------------------

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def gpsUrl(lat, lon, zoom):
	(x, y) = deg2num(lat, lon, zoom)
	imUrl = "http://a.tile.openstreetmap.org/%s/%s/%s.png"%(zoom, x, y)
	return imUrl

def gpsImg(filename, lat, lon, zoom):
	
	x, y = deg2num(lat, lon, zoom)	
	upperLeftLat, upperLeftLon = num2deg(x, y, zoom)
	upperRightLat, upperRightLon = num2deg(x+1, y, zoom)
	bottomLeftLat, bottomLeftLon = num2deg(x, y+1, zoom)
	
	#print("Upper Left: %s - %s"%(upperLeftLat, upperLeftLon))
	#print("Upper Right: %s - %s"%(upperRightLat, upperRightLon))
	#print("Bottom Left: %s - %s"%(bottomLeftLat, bottomLeftLon))
	
	deltaLat = upperLeftLat - bottomLeftLat
	deltaLon = upperRightLon - upperLeftLon
	
	#print("X,Y: %s %s"%(dotX, dotY))
	
	try:
		file = urllib.urlopen(gpsUrl(lat, lon, zoom))
		imRead = cStringIO.StringIO(file.read())
		im = PIL.Image.open(imRead)
		draw = ImageDraw.Draw(im)
		
		imgHeight, imgWidth = im.size 
		
		dotY = imgWidth - int(float((lat - bottomLeftLat) * imgHeight) / float(deltaLat))
		dotX = int(float((lon - upperLeftLon) * imgWidth) / float(deltaLon))
		
		rectWidth = 10
		draw.rectangle([dotX-rectWidth, dotY-rectWidth, dotX+rectWidth, dotY+rectWidth], outline=0)
		im.save(filename)
		
		return 0
	
	except:
		print("Unable to download image for GPS data from OpenStreetMap")
		return 1

def reverseGeocode(lat, lon, zoom):
	try:
		url = "http://nominatim.openstreetmap.org/reverse?format=xml&lat=%s&lon=%s&zoom=%s&addressdetails=1"%(lat, lon, zoom)
		dom = minidom.parse(urllib.urlopen(url))
		address = dom.getElementsByTagName('result')
		if (len(address) >= 1):
			return address[0].firstChild.toxml()
	except:
		print("Unable to fetch reverse geocode data")
		return None
	
	return None

gpsData = exifData.decodeGpsData(exifData.getGpsData())

if (gpsData != None):

	Story.append(Paragraph("EXIF Location data", styles['Heading2']))

	lat = gpsData['lat']
	lon = gpsData['lon']
	
	address = reverseGeocode(lat, lon, 14)
	if (address != None):
		Story.append(Paragraph("The photo seems to have been shot in: \"%s\""%address, styles['Normal']))
		Story.append(Spacer(1, 10))

	imgDim = 2.3*inch
	
	res1 = gpsImg("temp01.png", lat, lon, 7)
	res2 = gpsImg("temp02.png", lat, lon, 10)
	res3 = gpsImg("temp03.png", lat, lon, 13)
	
	if (res1 == 0 and res2 == 0 and res3 == 0):
	
		im1 = Image("temp01.png", imgDim, imgDim)
		im2 = Image("temp02.png", imgDim, imgDim)
		im3 = Image("temp03.png", imgDim, imgDim)
	
		t=Table([[im1, im2, im3]], colWidths=[imgDim + 10, imgDim + 10, imgDim + 10])
		t.setStyle(tableStyleImg)
		Story.append(t)
		
		Story.append(Paragraph("Tiles provided by OpenStreetMap.org (c) OpenStreetMap contributors, CC-BY-SA", styles['Caption']))
		
		Story.append(Spacer(10, 20))

# ------- EXIF Section ----------------------------------------------------

headerData = [
	[
		Paragraph("Key", styles["Small"]), 
		Paragraph("Name", styles["Small"]), 
		Paragraph("Content", styles["Small"])
	]
]
t=Table(headerData, colWidths=[40, 130, 360])
t.setStyle(tableStyleGray)
Story.append(t)
Story.append(Spacer(1, 2))

for exif in exifs:
	if (exif['tag'] not in [37500]):

		try:
			valPar = Paragraph(str(exif['value']), styles['Small'])
		except:
			valPar = Paragraph(unicode(exif['value'], errors='replace'), styles['Small'])
			for line in exifData.valInHex(exif).split('\n'):	
				if (len(line) > 0):
					exif['comments'].append(line)
			
		elementData = [
			[
				Paragraph(str(exif['tag']), styles["Small"]), 
				Paragraph(str(exif['decoded']), styles["Small"]), 
				valPar
			]
		]
		
		for line in exif['comments']:
			elementData.append(['', '', Paragraph(str(line), styles["CodeNoIndent"])])
		
		t=Table(elementData, colWidths=[40, 130, 360])
		t.setStyle(tableStyleSmall)
		Story.append(t)
		
		Story.append(Spacer(1, 2))

for exif in exifs:
	
	# Manage Maker notes in separate pages
	if (exif['tag'] == 37500):
		
		Story.append(PageBreak())
		Story.append(Paragraph("Maker Notes", styles['Heading2']))
		
		elementData = [
			[
				Paragraph(str(exif['tag']), styles["Small"]), 
				Paragraph(str(exif['decoded']), styles["Small"]), 
				Paragraph(str(exif['value']), styles["Small"]), 
			]
		]
		
		for line in exif['comments']:
			elementData.append(['', '', Paragraph(str(line), styles["CodeNoIndent"])])
		
		t=Table(elementData, colWidths=[40, 130, 360])
		t.setStyle(tableStyleStandard)
		Story.append(t)

# ------- DOC Generation ----------------------------------------------------

doc = SimpleDocTemplate(reportFileName, pagesize=letter,
                        rightMargin=40,leftMargin=40,
                        topMargin=40,bottomMargin=40)

doc.build(Story)