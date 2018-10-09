from django.db import models
from django.db.models.signals import post_init
from PIL import Image
from imagehash import whash, hex_to_hash
import os

# Create your models here.

class ImageModel(models.Model):
	id = models.BigAutoField(primary_key=True, null=False)
	hash = models.CharField(max_length=16)
	path = models.TextField()
	docfile = models.FileField(
		upload_to='documents'+os.path.sep+'%Y'+os.path.sep+'%m'+os.path.sep+'%d',
		null=True
	)
	dbName = models.TextField(null=False, default="main")

	# Matcher - match the object against the images in the database and
	# return a list of ImageModels that match within maxDiff percent.
	def findMatches(self, maxDiff):
		theHash = self.hash
		results = []
		allImages = ImageModel.objects.all()
		for Image in allImages:
			a = hex_to_hash(Image.hash)
			b = hex_to_hash(theHash)
			difference = 100*(a - b)/(len(a.hash)**2)
			if(difference < maxDiff):
				results.append(Image)
		return results

class UserDatabase(models.Model):
	dbName = models.TextField(primary_key=True, null=False)
	dbOwner = models.TextField(null=False, default='admin')


