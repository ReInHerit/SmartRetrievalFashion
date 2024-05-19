
# Smart Retrieval for Fashion

A search engine for fashion images using CLIP fine-tuned for fashion image retrieval.

![Smart Retrieval logo](static/Image/smart_retrieval_logo.jpg)


## About Project

This application has been developed within the [ReInHerit Project](https://www.reinherit.eu).

### Built with
* [Python](https://www.python.org/)
* [PyTorch](https://pytorch.org/)
* [Torchvision](https://pytorch.org/vision/stable/index.html)
* [CLIP](https://github.com/openai/CLIP)
* [FashionClip](https://github.com/patrickjohncyh/fashion-clip.git)
* [Flask](https://flask.palletsprojects.com/en/2.0.x/)
* [Bootstrap](https://getbootstrap.com/)
## Installation
For the installation use Docker, the Dockerfile is provided in the repository.
For development use .devcontainer provided in the repository.

### Setting UP
Install this project with Conda, creating a new environment and installing the requirements with:

```bash
  conda create --name SmartRetrievalFashion python=3.11
  conda activate SmartRetrievalFashion
  pip install -r requirements.txt
```

Alternatively use the provided Dockerfile to build the image and run the container.

Datasets should be stored in this directory structure:
```
dataset
│
└───Images
│   │
│   └───sets of .jpeg|.jpg|.png images in one directory for each collection
│
└───Metadata
│   │
│   └───sets of .json files describing the images, one file for each collection
│
└───Fclip
│   │
│   └───sets of .pkl files containing the FashionCLIP descriptors for each image, one file for each collection
│
└───dataset.json  describing the collections
```

A sample dataset is provided as reference for the format.

When the app is started the first time it will parse the dataset directory and build the ChromaDB index used to search the images.
It will also download FashionClip model that will be installed in the environment or Docker image.

## Authors

- [@MarcoBertini](https://www.github.com/mbertini)
- [@FilippoPrincipi](https://www.github.com/no-made)
- [@MugnaiLorenzo](https://www.github.com/MugnaiLorenzo)

