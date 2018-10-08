from PIL import Image
from imagehash import whash, hex_to_hash
from steelsensor.models import ImageModel
import os

# Matcher - takes a StoredImage object and a float "maxDiff" and
# returns a list of ImageModels that match within maxDiff percent.
def match(theImage, maxDiff):

	theHash = theImage.hash

	# theHash = whash(Image.open("media"+os.path.sep+theImage.docfile.name))

	results = []

	allImages = ImageModel.objects.all()
	for Image in allImages:
		a = hex_to_hash(Image.hash)
		b = hex_to_hash(theHash)
		difference = 100*(a - b)/(len(a.hash)**2)
		#print(difference)
		if(difference < maxDiff):
			results.append(Image)
	#print(results)
	return results
