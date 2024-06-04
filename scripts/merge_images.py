from PIL import Image, ImageChops
import os
import argparse

# Define the argument parser
parser = argparse.ArgumentParser(description='Merge all images in a folder.')
parser.add_argument('--folder', '-f', type=str, help='Path to the folder containing the images')
parser.add_argument('--output', '-o', type=str, help='Path to the output merged image')
args = parser.parse_args()

# Get a list of all the image files in the folder
image_files = [os.path.join(args.folder, f) for f in os.listdir(args.folder) if f.endswith('.jpg')]

# Open all the images and get their dimensions
images = []
widths = []
heights = []
for f in image_files:
    image = Image.open(f)
    images.append(image)
    widths.append(image.width)
    heights.append(image.height)

# Compute the total width and height of the merged image
max_width = max(widths)
max_height = max(heights)

# Create a new blank image with the required size
new_image = Image.new('RGB', (max_width, max_height))
scalar = 3 / len(widths)
# Paste the individual images onto the new image
for i in range(len(images)):
    mul_img = images[i].point(lambda x: int(x * scalar) if x > 128 else 0)
    new_image = ImageChops.add(new_image, mul_img)

# Save the merged image
new_image.save(args.output)
