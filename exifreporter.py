#!/usr/bin/env python

from exifviewer import ExifData
import sys, math

import PIL, urllib, cStringIO
from PIL import ImageDraw
	
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, Image, PageBreak, Table, TableStyle, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def usage():
	print("")
	print("PicciMario EXIF reported v. 0.1")
	print("mario.piccinelli@gmail.com")
	print("")
	print("Usage:")
	print("exifreporter.py filename")
	print("")

filename = ""

if (len(sys.argv) <= 1):
	usage()
	sys.exit(1)
else:
	filename = sys.argv[1]

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
		leading=8.8,
		firstLineIndent=0,
		leftIndent=0
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

Story.append(Paragraph("Image analysis report", styles["Title"]))

thumbWidth = 3*inch
thumbHeight = exifData.imageHeight * (float(thumbWidth) / float(exifData.imageWidth))

im = Image(filename, thumbWidth, thumbHeight)

imgData = Table(
	[
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
		]
	],
	colWidths=[94, 210]
)
imgData.setStyle(tableStyleStandard)

t=Table([[im, imgData]], colWidths=[3*inch+6, 310])
t.setStyle(tableStyleImg)
Story.append(t)

Story.append(Spacer(10, 20))

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
	

gpsData = exifData.decodeGpsData(exifData.getGpsData())

if (gpsData != None):

	lat = gpsData['lat']
	lon = gpsData['lon']
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
	elementData = [
		[
			Paragraph(str(exif['tag']), styles["Small"]), 
			Paragraph(str(exif['decoded']), styles["Small"]), 
			Paragraph(str(exif['value']), styles["Small"])
		]
	]
	for line in exif['comments']:
		elementData.append(['', '', Paragraph(str(line), styles["CodeNoIndent"])])
	
	t=Table(elementData, colWidths=[40, 130, 360])
	t.setStyle(tableStyleStandard)
	Story.append(t)
	
	Story.append(Spacer(1, 2))

# ------- DOC Generation ----------------------------------------------------

doc = SimpleDocTemplate("form_letter.pdf",pagesize=letter,
                        rightMargin=72,leftMargin=72,
                        topMargin=72,bottomMargin=18)

doc.build(Story)