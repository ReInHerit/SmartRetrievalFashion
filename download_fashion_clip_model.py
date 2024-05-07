from fashion_clip.fashion_clip import FashionCLIP


def download_model():
    print("Starting to download model...")
    FashionCLIP('fashion-clip')
    print("Download model completed.")


if __name__ == '__main__':
    download_model()
