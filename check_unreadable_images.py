import os
from PIL import Image
from multiprocessing import Pool
import argparse
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description='Check unreadable images in a directory')
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-d", '--directory', type=str, help='Images directory name', required=True)
    parser.add_argument("-l", '--log-file', type=str, help='Log file name', default="unreadable_images.log")
    return parser.parse_args()


def check_image_readable(image_path):
    try:
        with Image.open(image_path) as img:
            img.load()
        return True, image_path
    except Exception as e:
        return False, image_path


def log_unreadable_images(results, log_file):
    with open(log_file, "w") as f:
        for result in results:
            if not result[0]:
                f.write(result[1] + "\n")


def main():
    args = parse_args()
    directory = args.directory
    log_file = args.log_file
    print(f"Checking images in {directory} for readability...")
    print(f"Logging unreadable images in {log_file}")
    image_files = [os.path.join(directory, f) for f in os.listdir(directory) if
                   os.path.isfile(os.path.join(directory, f))]

    # Set up multiprocessing pool
    pool = Pool()
    print(f"Checking {len(image_files)} images...")
    # Map the function to check image readability to each image file in parallel
    results = list(tqdm(pool.imap(check_image_readable, image_files), total=len(image_files)))

    # Close the pool to prevent any more tasks from being submitted to it
    pool.close()

    # Wait for the worker processes to exit
    pool.join()
    print("All images checked.")
    # Print results
    for result in results:
        if result[0]:
            print(f"Image at {result[1]} is readable.")
        else:
            print(f"Image at {result[1]} is not readable.")

    # Log unreadable images
    log_unreadable_images(results, log_file)
    print(f"Unreadable images logged in {log_file}")


if __name__ == "__main__":
    main()
