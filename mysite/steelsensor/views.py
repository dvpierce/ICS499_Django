from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from django.template import RequestContext
from django.urls import reverse

from steelsensor.models import ImageModel
from steelsensor.forms import DocumentForm

import os
import sys

from steelsensor.matcher import match
from PIL import Image
from imagehash import whash, hex_to_hash

# Create your views here.

def index(request):
	form = DocumentForm()
	documents = []
	return render(request, 'index.html', {'documents': documents, 'form': form})

def results(request):
	if request.method == 'POST':
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():
			# Create thing and save file.
			thisDocfile = request.FILES['docfile']
			newImageModel = ImageModel(docfile = thisDocfile)
			newImageModel.save()

			imageHashValue = whash(Image.open(newImageModel.docfile.path))

			print(newImageModel.docfile.path)
			# Add filename and hash
			newImageModel.path = thisDocfile.name
			newImageModel.hash = str(imageHashValue)
			newImageModel.save()

		results = match(newImageModel, 30)
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

