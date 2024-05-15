import os
import shutil
import random
import argparse
import glob

# Define the arguments
parser = argparse.ArgumentParser(description='Randomly subsample a dataset.')
parser.add_argument('-i', '--source_directory', type=str, required=True, help='Source directory containing all the images')
parser.add_argument('-o', '--destination_directory', type=str, required=True, help='Destination directory where the selected images will be copied')
parser.add_argument('-n', '--num_images_to_copy', type=int, required=False, default=10000, help='Number of images to be copied')
args = parser.parse_args()

# Source directory containing all the images
source_directory = args.source_directory
if not os.path.exists(source_directory):
    raise ValueError(f"Source directory '{source_directory}' does not exist.")

# Destination directory where the selected images will be copied
destination_directory = args.destination_directory
if not os.path.exists(destination_directory):
    raise ValueError(f"Destination directory '{destination_directory}' does not exist.")

# Number of images to be copied
num_images_to_copy = args.num_images_to_copy

print(f"Source directory: {source_directory}")
print(f"Destination directory: {destination_directory}")
print(f"Number of images to copy: {num_images_to_copy}")

print("Reading image filenames...")
# List all jpeg, jpg, and png files in the directory
all_images = (glob.glob(os.path.join(source_directory, '*.[jJ][pP][gG]')) +
              glob.glob(os.path.join(source_directory, '*.[jJ][pP][eE][gG]')) +
              glob.glob(os.path.join(source_directory, '*.[pP][nN][gG]')))
print(f"Number of images found: {len(all_images)}")

print("Selecting images...")
# Randomly select requested images
selected_images = random.sample(all_images, num_images_to_copy)

# Create the destination directory if it doesn't exist
if not os.path.exists(destination_directory):
    os.makedirs(destination_directory)

print("Copying images...")
# Copy selected images to the destination directory
for image in selected_images:
    source_path = os.path.join(source_directory, os.path.basename(image))
    destination_path = os.path.join(destination_directory, os.path.basename(image))
    shutil.copyfile(source_path, destination_path)

print("Images copied successfully.")
