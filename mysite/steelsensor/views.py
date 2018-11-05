from django.shortcuts import render, redirect

from django.http import HttpResponse, HttpResponseRedirect

from django.template import RequestContext
from django.urls import reverse

from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage

from steelsensor.models import ImageModel, UserDatabase
from steelsensor.forms import DocumentForm, dbManageForm

import os
import sys
import random

from PIL import Image
from imagehash import whash, hex_to_hash

# Create your views here

################################################################################
#
# class ImageModel(models.Model):
#	hash = models.CharField(max_length=16)
#	path = models.TextField()
#	randomKey = models.TextField(primary_key=True)
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

ValidFileTypes = [ 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif', 'tiff', 'zip' ]

def index(request):
	form = DocumentForm()
	documents = []
	databases = [ "main" ] + [ x.dbName for x in UserDatabase.objects.filter(dbOwner=request.user) ]
	return render(request, 'index.html', {'documents': documents, 'form': form, 'databases': databases})

def zipHandler(request):
	dbName = request.POST['dbSelect']
	zipFile = request.FILES['docfile']
	fs = FileSystemStorage()
	filename = fs.save(zipFile.name, zipFile)
	print(filename)
	print(fs.url(filename))
	print(fs.location)
	FileAbsPath = fs.location + os.path.sep + filename
	print(FileAbsPath)
	return

def results(request):
	if request.method == 'POST':
		dbMatchThreshold=30
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():

			# Check if user has r/w permissions on database.
			try:
				requesteddbName = request.POST['dbSelect']
				requestedDB = UserDatabase.objects.get(dbOwner = request.user.username, dbName = requesteddbName)
				# print(requesteddbName, request.user.username, requestedDB)
			except:
				return HttpResponse("<html><body><p>There was an error accessing the requested database: %s. Either it does not exist or you do not have write permissions.</p><p><a href=/steelsensor>Go Home.</a></p></body></html>" % requesteddbName)


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

		else:
			return render(request, 'error.html', {'errorCode': "Invalid Form Received." })

		results = newImageModel.findMatches(dbMatchThreshold)
	else:
		results = []
	return render(request, 'results.html', {'original' : str(newImageModel.docfile), 'results': [ str(x.docfile) for x in results]})

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
		databases = [ db ]
	else:
		databases = [ x.dbName for x in UserDatabase.objects.filter(dbOwner=request.user) ]
		if str(request.user) in "admin": databases.append("main")

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
	searchImage = ImageModel.objects.get(docfile = request.GET.get('imgURL', ''))
	# Delete file from local file system
	localPath = searchImage.docfile.path
	os.remove(localPath)
	print("Deleting " + localPath)
	# Delete the imageModel
	searchImage.delete()

	return HttpResponse("<html><body><p>Deleted "+localPath+"</p><p><a href=/steelsensor/>Go Home</a></p><body></html>")

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

	return redirect('dbmanage')

def deleteImages(request):
	return HttpResponse("<html><body><p>This is where we let users delete images that they've uploaded. (Not yet implemented.)</p><p><a href=/steelsensor/>Go Home</a></p></body></html>")



