from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from django.template import RequestContext
from django.urls import reverse

from steelsensor.models import ImageModel, UserDatabase
from steelsensor.forms import DocumentForm

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

ValidFileTypes = [ 'png', 'jpg', 'jpeg', 'gif' ]

def index(request):
	form = DocumentForm()
	documents = []
	databases = [ "main" ] + [ x.dbName for x in UserDatabase.objects.filter(dbOwner=request.user) ]
	return render(request, 'index.html', {'documents': documents, 'form': form, 'databases': databases})

def results(request):
	if request.method == 'POST':
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():

			# Create thing and save file.
			thisDocfile = request.FILES['docfile']
			newImageModel = ImageModel(docfile = thisDocfile, dbName = request.POST['dbSelect'][0], path = thisDocfile.name)

			# Check file name against allowed formats.
			if thisDocfile.name.split('.')[-1].lower() not in ValidFileTypes:
				print("Invalid file type submitted.")
				return render(request, 'error.html', {'errorCode': "Invalid File Type: " + thisDocfile.name.split('.')[-1] })

			newImageModel.save()

			# Add image hash
			imageHashValue = whash(Image.open(newImageModel.docfile.path))
			newImageModel.hash = str(imageHashValue)
			newImageModel.save()
		else:
			return render(request, 'error.html', {'errorCode': "Invalid Form Received." })

		results = newImageModel.findMatches(30)
	else:
		results = []
	return render(request, 'results.html', {'results': [x.docfile.path.split(os.getcwd())[1] for x in results]})

def browse(request):
	documents = ImageModel.objects.all()
	return render(request, 'browse.html', {'documents': [ x.docfile.path.split(os.getcwd())[1] for x in documents ] } )

def admintools(request):
	if request.user.is_authenticated:
		return HttpResponse("You are an authenticated user and should be allowed to see this page.")
	else:
		return HttpResponse("You're a stranger.")


def dbcreate(request):
	return HttpResponse("<html><body><p>This is where we create databases. (Not yet implemented.)</p><p><a href=/steelsensor/>Go Home</a></p></body></html>")

def dbdelete(request):
	return HttpResponse("<html><body><p>This is where we delete databases. (Not yet implemented.)</p><p><a href=/steelsensor/>Go Home</a></p></body></html>")

def deleteImages(request):
	return HttpResponse("<html><body><p>This is where we let users delete images that they've uploaded. (Not yet implemented.)</p><p><a href=/steelsensor/>Go Home</a></p></body></html>")



