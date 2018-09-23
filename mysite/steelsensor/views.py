from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from django.template import RequestContext
from django.urls import reverse

from steelsensor.models import StoredImage
from steelsensor.forms import DocumentForm

# Create your views here.

def index(request):
	# Handle file upload
	if request.method == 'POST':
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():
			newdoc = StoredImage(docfile = request.FILES['docfile'])
			newdoc.save()

			# Redirect to the document list after POST
			return HttpResponseRedirect(reverse('index'))
	else:
		form = DocumentForm() # A empty, unbound form

	# Load documents for the list page
	documents = StoredImage.objects.all()
	# Render list page with the documents and the form
	return render(request, 'index.html', {'documents': documents, 'form': form})

def results(request):
	return HttpResponse("This is a results page view placeholder.")

def admintools(request):
	if request.user.is_authenticated:
		return HttpResponse("You are an authenticated user and should be allowed to see this page.")
	else:
		return HttpResponse("You're a stranger.")

