from PIL import Image
from imagehash import whash, hex_to_hash
from steelsensor.models import StoredImage, ImageModel
import os

# Matcher - takes a StoredImage object and a float "maxDiff" and
# returns a list of ImageModels that match within maxDiff percent.
def match(theImage, maxDiff):

	theHash = whash(Image.open("media"+os.path.sep+theImage.docfile.name))
	results = []

	imageHashes = ImageModel.objects.all()
	for hash in imageHashes:
		# print(hash.hash, hash.path)
		results.append(hash)
	# print(results)
	return results
