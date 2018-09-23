from django.db import models

# Create your models here.

class ImageModel(models.Model):
	fingerprint = models.CharField(max_length=200)
	path = models.CharField(max_length=200)

class StoredImage(models.Model):
	docfile = models.FileField(upload_to='documents/%Y/%m/%d')
