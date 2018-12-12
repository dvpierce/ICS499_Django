from django.shortcuts import render, redirect

from django.http import HttpResponse, HttpResponseRedirect

from django.template import RequestContext
from django.urls import reverse

from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage
from django.core.files import File

from steelsensor.models import ImageModel, UserDatabase
from steelsensor.forms import DocumentForm, dbManageForm

import os
import sys
import random
import subprocess

from PIL import Image
from imagehash import whash, hex_to_hash

# Create your views here

################################################################################
#
# class ImageModel(models.Model):
#	hash = models.CharField(max_length=16)
#	path = models.TextField()
#	docfile = models.FileField(
#		upload_to='documents'+os.path.sep+'%Y'+os.path.sep+'%m'+os.path.sep+'%d',
#		null=True
#	)
#	dbName = models.TextField(null=False, default="main")
#
# class UserDatabase(models.Model):
#	dbName = models.TextField(primary_key=True, null=False)
#	dbOwner = models.TextField(null=False, default="admin")
#
#
################################################################################

################################################################################
# Utility functions and constants. One could argue that this should go in
# a separate file, and one would probably be right.
################################################################################

ValidFileTypes = [ 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif', 'tiff', 'zip' ]

def zipHandler(request):
	dbName = request.POST['dbSelect']
	zipFile = request.FILES['docfile']
	fs = FileSystemStorage()
	# Save the zip file to local file system.
	filename = fs.save(zipFile.name, zipFile)

	# Expand the zip file
	ZipFileAbsPath = fs.location + os.path.sep + filename
	ZipFileUnzipPath = fs.location + os.path.sep + "temp"
	subprocess.call(["unzip", "-o", ZipFileAbsPath, "-d", ZipFileUnzipPath])

	# Find all the files of allowable file types in the directory.
	FileNames = [ fileName for fileName in os.listdir(ZipFileUnzipPath) if fileName.split('.')[-1].lower() in ValidFileTypes ]
	# print(FileNames)
	FileAbsPaths = [ (ZipFileUnzipPath + os.path.sep + FileName) for FileName in FileNames ]
	# print(FileAbsPaths)

	# process each file.
	for filePath in FileAbsPaths:
		try:
			# print(filePath)
			with open(filePath, 'rb') as f:
				# pass the file data and the filename to a Django File object.
				djangofile = File(f, name=filePath.split(os.path.sep)[-1])
				# Create a new ImageModel with the file object - this will observe the upload_to
				# default and save a copy of the file in the /media/documents directory.
				newImageModel = ImageModel(
					docfile = djangofile,
					dbName = request.POST['dbSelect'],
					path = filePath.split(os.path.sep)[-1]
				)
				newImageModel.save()

			# Add image hash
			imageHashValue = whash(Image.open(newImageModel.docfile.path))
			newImageModel.hash = str(imageHashValue)
			newImageModel.save()
		except Exception as ex:
			# There was some kind of issue processing this particular file.
			# Don't worry about it, just do the rest, if there are any.
			continue

	# clean up after self
	print("Deleting temporary data")
	subprocess.call(["rm", "-Rf", ZipFileUnzipPath])
	subprocess.call(["rm", "-Rf", ZipFileAbsPath])
	return

################################################################################
# Views
################################################################################

def index(request):
	form = DocumentForm()
	documents = []
	databases = [ "main" ] + [ x.dbName for x in UserDatabase.objects.filter(dbOwner=request.user) ]
	return render(request, 'index.html', {'documents': documents, 'form': form, 'databases': databases})

def results(request):
	if request.method == 'POST':
		dbMatchThreshold=30
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():
			# If the current user is the UnAuth'd user, show the "main" database, but set a flag to delete the image later.
			if str(request.user) == "AnonymousUser": UserAnon = True
			else: UserAnon = False

			# Interestingly, for unauthenticated users, while request.user has a String value of "AnonymousUser",
			# request.user.username has a null string value. This is annoying.

			# Check if user has r/w permissions on database.
			# If the current user is admin and they've selected the "main" database, it's a special case
			# that is foolishly not included in our database model.
			if not ( request.POST['dbSelect'] == "main" and ( request.user.username in [ "admin", "" ] ) ):
				try:
					# Check to make sure that the currently logged in user owns the requested database.
					requesteddbName = request.POST['dbSelect']
					requestedDB = UserDatabase.objects.get(dbOwner = request.user.username, dbName = requesteddbName)
					# print(requesteddbName, request.user.username, requestedDB)
				# If the logged in user does NOT own the currently selected database, return an error.
				except Exception as ex:
					# print(ex)
					return render(request, 'error.html', {'errorCode': "There was an error accessing the requested database: %s. Either it does not exist or you do not have write permissions." % requesteddbName })

			# Create thing and save file.
			thisDocfile = request.FILES['docfile']
			newImageModel = ImageModel(docfile = thisDocfile, dbName = request.POST['dbSelect'], path = thisDocfile.name)

			# Check file name against allowed formats.
			if thisDocfile.name.split('.')[-1].lower() not in ValidFileTypes:
				# print("Invalid file type submitted.")
				return render(request, 'error.html', {'errorCode': "Invalid File Type: " + thisDocfile.name.split('.')[-1] })

			# Check for zip file.
			if thisDocfile.name.split('.')[-1].lower() in 'zip':
				zipHandler(request)
				return HttpResponse("<p>File uploaded and images processed.</p><p><a href=/steelsensor/>Go Home</a></p>")

			newImageModel.save()

			# Add image hash
			imageHashValue = whash(Image.open(newImageModel.docfile.path))
			newImageModel.hash = str(imageHashValue)
			newImageModel.save()

			try:
				dbMatchThreshold = int(request.POST['matchingThreshold'])
			except:
				pass

			# Find matches
			results = newImageModel.findMatches(dbMatchThreshold)

			# if the current user is anonymous, delete the newImageModel from the database immediately.
			if UserAnon:
				# Delete file from local file system and database
				localPath = newImageModel.docfile.path
				os.remove(localPath)
				newImageModel.delete()
				return render(request, 'results.html', {'original' : "../favicon.ico", 'results': [ str(x.docfile) for x in results]})
			else:
				return render(request, 'results.html', {'original' : str(newImageModel.docfile), 'results': [ str(x.docfile) for x in results]})
		else:
			return render(request, 'error.html', {'errorCode': "Invalid Form Received." })

	else:
		results = []
		return render(request, 'results.html', {'original' : "../favicon.ico", 'results': [ str(x.docfile) for x in results]})

def browse(request):
	page = request.GET.get('p', '')
	maxPage = request.GET.get('count', '')
	db = request.GET.get('db', '')
	if page and maxPage:
		try:
			page = int(page)
			maxPage = int(maxPage)
		except:
			page = 1
			maxPage = 5
	else:
		page = 1
		maxPage = 5

	# Determine which images the current user should be allowed to view.
	# Or restrict to provided search pattern.

	if db:
		print(db, "requested")
		databases = [ db ]
	else:
		databases = [ x.dbName for x in UserDatabase.objects.filter(dbOwner=request.user) ] + [ "main" ]

	allImages = ImageModel.objects.filter(dbName__in=databases)
	pagedImages = Paginator(allImages, maxPage)

	if (page < 1): page = 1
	if (page > pagedImages.num_pages): page = pagedImages.num_pages

	allImages = pagedImages.page(page)

	if ( page < pagedImages.num_pages ):
		nextPageLink = "?p=%d&count=%d" % ( page + 1, maxPage)
	else:
		nextPageLink = None
	if ( page > 1 ):
		prevPageLink = "?p=%d&count=%d" % ( page - 1, maxPage)
	else:
		prevPageLink = None

	if db:
		if nextPageLink: nextPageLink += "&db="+db
		if prevPageLink: prevPageLink += "&db="+db

	# print(prevPageLink, page, nextPageLink)
	return render(request, 'browse.html', {'documents': [ str(x.docfile) for x in allImages ], 'nextPageLink' : nextPageLink, 'prevPageLink' : prevPageLink, 'pageNum' : page } )

def browsematches(request):
	searchImage = ImageModel.objects.get(docfile = request.GET.get('imgURL', ''))
	results = searchImage.findMatches(30)

	return render(request, 'browsematches.html', {'original' : str(searchImage.docfile), 'matches' : [ str(x.docfile) for x in results ] })

def deleteImage(request):
	# Find the image requested
	try:
		searchImage = ImageModel.objects.get(docfile = request.GET.get('imgURL', ''))
		requesteddbName = searchImage.dbName
	except:
		return render(request, 'error.html', {'errorCode' : "Image not found."})

	# Verify that user has r/w on this database.
	if not ( (request.user.username in "admin") and (requesteddbName in "main") ):
		try:
			requestedDB = UserDatabase.objects.get(dbOwner = request.user.username, dbName = requesteddbName)
		except:
			# Error condition: the database with name ___ is not owned by the requesting user.
			return render(request, 'error.html', {'errorCode' : "You do not have permission to delete this image." })


	# Delete file from local file system
	localPath = searchImage.docfile.path
	os.remove(localPath)
	print("Deleting " + localPath)
	# Delete the imageModel
	searchImage.delete()

	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	# return HttpResponse("<html><body><p>Deleted "+localPath+"</p><p><a href=/steelsensor/>Go Home</a></p><body></html>")

def admintools(request):
	if request.user.is_authenticated:
		return HttpResponse("You are an authenticated user and should be allowed to see this page.")
	else:
		return HttpResponse("You're a stranger.")


def dbmanage(request):
	if request.method == "POST":
		form = dbManageForm(request.POST)
		if form.is_valid():
			newDatabase = UserDatabase(dbName = request.POST['NewdbName'], dbOwner = request.user.username)
			newDatabase.save()
		return redirect('dbmanage')
	else:
		form = dbManageForm()
		databases = [ x.dbName for x in UserDatabase.objects.filter(dbOwner=request.user) ]
		return render(request, 'dbmanage.html', { 'form' : form, 'databases' : databases } )


def dbdelete(request):
	dbToDelete = request.GET.get('db','')
	# print(dbToDelete)

	# Verify that user has r/w on this database.
	try:
		requestedDB = UserDatabase.objects.get(dbOwner = request.user.username, dbName = dbToDelete)
	except:
		# Error condition: the database with name ___ is not owned by the requesting user.
		return render(request, 'error.html', {'errorCode' : "You do not have permission to delete this database." })

	# Delete all images with this database name
	for dbImg in ImageModel.objects.filter(dbName=dbToDelete):
		# Delete file from local file system
		localPath = searchImage.docfile.path
		os.remove(localPath)
		print("Deleting " + localPath)
		# Delete the imageModel
		searchImage.delete()

	requestedDB.delete()
	# print("Database deleted")

	return redirect('dbmanage')

def deleteImages(request):
	return HttpResponse("<html><body><p>This is where we let users delete images that they've uploaded. (Not yet implemented.)</p><p><a href=/steelsensor/>Go Home</a></p></body></html>")



