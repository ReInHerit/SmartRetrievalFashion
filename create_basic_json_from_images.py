import glob
import os
import re
import argparse
import json


def parse_args():
    parser = argparse.ArgumentParser(description='Extract brand name from image filename')
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-d", '--directory', type=str, help='Images directory name', required=True)
    parser.add_argument("-b", '--separate-brands', help='Create separate JSON files for each brand', action="store_true", default=False)
    return parser.parse_args()


def extract_brand_name(filename):
    pattern = r'^([a-zA-Z\d_]+?)(?:_[a-zA-Z]+?\d+_?\d*\.jpg)$'
    match = re.match(pattern, filename)
    if match:
        brand_name = match.group(1)
        return brand_name.replace('_', ' ')
    else:
        return ""


def create_json_files(images_per_brand: dict, output_dir, verbose: bool, separate_brands=False):
    if not separate_brands:
        items = []
        for brand_name, filenames in images_per_brand.items():
            items.extend(create_element_json_entry(brand_name, filenames))
        output_filepath = output_dir + os.sep + "collection_1.json"
        save_json_file(items, output_filepath, verbose)
    else:
        for brand_name, filenames in images_per_brand.items():
            items = create_element_json_entry(brand_name, filenames)
            # Create a new JSON file named after the brand
            output_filepath = output_dir + os.sep + brand_name.replace(' ', '_') + ".json"
            save_json_file(items, output_filepath, verbose)


def save_json_file(items, output_filepath, verbose):
    if verbose:
        print(f"Saving items {len(items)} in {output_filepath}...")
    with open(output_filepath, 'w') as f:
        json.dump(items, f, indent=4)


def create_element_json_entry(brand_name, filenames):
    items = []
    for filename in filenames:
        # Get the directory path and the filename
        dir_path = os.path.dirname(filename)
        # Split the directory path and get the last directory
        last_dir = dir_path.split(os.sep)[-1]
        article_id = os.path.splitext(os.path.basename(filename))[0]
        # Create a dictionary for each filename with the same format as the items in collection_1.json
        item = {
            "article_id": article_id,  # Use the filename as the article_id
            "prod_name": brand_name,  # Use the brand_name as the prod_name
            "product_type_name": "",  # Fill in the appropriate values
            "product_group_name": "",
            "colour_group_name": "",
            "detail_desc": "",
        }
        items.append(item)
    return items


def create_dataset_json(images_per_brand: dict, images_directory: str, dataset_directory, verbose: bool,
                        separate_brands: bool):
    dataset = []
    collection_id = 1
    if not separate_brands:
        item = {
            "collection": collection_id,
            "image_path": os.path.relpath(images_directory, "."),  # The directory where the images for the brand are stored
            "metadata_path": os.path.relpath(dataset_directory, ".") + os.sep + "Metadata" + os.sep + "collection1.json",  # The path to the JSON file for the brand
            "fclip_path": "",  # Fill in the appropriate value
            "name": "collection1",
            "representative": ""  # The first image in the list of images for the brand
        }
        dataset.append(item)
    else:
        for brand_name, filenames in images_per_brand.items():
            # Create a dictionary for each brand with the same format as the items in dataset.json
            brand_name_file = brand_name.replace(' ', '_') + ".json"
            item = {
                "collection": collection_id,
                "image_path": images_directory,  # The directory where the images for the brand are stored
                "metadata_path": dataset_directory + os.sep + brand_name_file,  # The path to the JSON file for the brand
                "fclip_path": "",  # Fill in the appropriate value
                "name": brand_name,
                "representative": filenames[0] if filenames else ""  # The first image in the list of images for the brand
            }
            dataset.append(item)
            collection_id += 1
    # Write the list to the new JSON file
    if verbose:
        print(f"Saving dataset.json with {len(dataset)} collections...")
    with open(dataset_directory + os.sep + "dataset.json", 'w') as f:
        json.dump(dataset, f, indent=4)


def main(args):
    input_directory = args.directory + os.sep + 'Images'
    metadata_directory = args.directory + os.sep + 'Metadata'
    if not os.path.exists(metadata_directory):
        os.makedirs(metadata_directory)
    dataset_directory = args.directory
    images_subdirs = [x[0] for x in os.walk(input_directory) if x[0] != input_directory]
    for images_subdir in images_subdirs:
        if args.verbose:
            print("Extracting brand names from image filenames in directory: ", input_directory)
        # List all jpeg, jpg, and png files in the directory
        images_filenames = (glob.glob(os.path.join(images_subdir, '*.[jJ][pP][gG]')) +
                            glob.glob(os.path.join(images_subdir, '*.[jJ][pP][eE][gG]')) +
                            glob.glob(os.path.join(images_subdir, '*.[pP][nN][gG]')))

        if args.verbose:
            print(f"Processing {len(images_filenames)} images...")
        images_per_brand = {}
        for filename in images_filenames:
            brand_name = extract_brand_name(os.path.basename(filename))
            if brand_name != "":
                if brand_name in images_per_brand:
                    images_per_brand[brand_name].append(filename)
                else:
                    images_per_brand[brand_name] = [filename]
            else:
                if "UNKNOWN BRAND" in images_per_brand:
                    images_per_brand["UNKNOWN BRAND"].append(filename)
                else:
                    images_per_brand["UNKNOWN BRAND"] = [filename]
        if args.verbose:
            print(f"Found {len(images_per_brand)} brands")
            print("Saving JSON files...")
        create_json_files(images_per_brand, metadata_directory, args.verbose, args.separate_brands)
        create_dataset_json(images_per_brand, images_subdir, dataset_directory, args.verbose, args.separate_brands)
        print(f"Collection {images_subdir} done!")
    if args.verbose:
        print("Done. Remind to create the .pkl files for the features and update the dataset.json file !")


if __name__ == "__main__":
    args = parse_args()
    main(args)
