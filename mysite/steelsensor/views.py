from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from django.template import RequestContext
from django.urls import reverse

from steelsensor.models import StoredImage
from steelsensor.models import ImageModel
from steelsensor.forms import DocumentForm

import os

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
			newdoc = StoredImage(docfile = request.FILES['docfile'])
			newdoc.save()
			imageHashValue = whash(Image.open("media"+os.path.sep+newdoc.docfile.name))
			newImageModel = ImageModel(path = newdoc.docfile.name, hash = str(imageHashValue))
			newImageModel.save()
		results = match(newdoc, 30)
	else:
		results = None
	return render(request, 'results.html', {'results': results})

def admintools(request):
	if request.user.is_authenticated:
		return HttpResponse("You are an authenticated user and should be allowed to see this page.")
	else:
		return HttpResponse("You're a stranger.")

