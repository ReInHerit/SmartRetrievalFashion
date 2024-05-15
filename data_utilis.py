import os
import pickle
import shutil

import torchvision.transforms.functional as F
import PIL.Image
import chromadb
import json
import random
from dotenv import load_dotenv
from more_itertools import batched

from fashion_clip.fashion_clip import FashionCLIP
from pathlib import Path
from typing import Optional
from torchvision.transforms import Compose, Resize, CenterCrop, ToTensor, Normalize
from chromadb.config import Settings

# Load the .env file
load_dotenv()

server_base_path = Path(__file__).absolute().parent.absolute()
dataset_path = os.getenv('DATASET_PATH', 'dataset')
dataset_root = Path(__file__).absolute().parent.absolute() / dataset_path
image_root = dataset_root / 'Images'
data_path = Path(__file__).absolute().parent.absolute() / 'data'
metadata_path = dataset_root / "Metadata"
chroma_path = str(dataset_root) + os.sep + "chroma"


def load():
    global chroma_client
    global fclip
    chroma_client = chromadb.PersistentClient(settings=Settings(
        persist_directory=chroma_path, allow_reset=True),
    )
    fclip = FashionCLIP('fashion-clip')


def update_chroma():
    print("UPDATE ChromaDB...")
    global chroma_client
    global fclip
    if not os.path.exists(chroma_path):
        os.makedirs(chroma_path)
    else:
        shutil.rmtree(chroma_path)
        os.makedirs(chroma_path)
    if is_load():
        chroma_client.reset()
    chroma_client = chromadb.PersistentClient(settings=Settings(
        persist_directory=chroma_path, allow_reset=True),
    )
    fclip = FashionCLIP('fashion-clip')
    f = open(dataset_root / 'dataset.json')
    data = json.load(f)
    for i in data:
        metadata_dict = {
            "id": i["collection"],
            "image_path": i["image_path"],
            "representative": i["representative"]
        }
        collection = chroma_client.create_collection(name=i['name'], metadata=metadata_dict)
        s = str(server_base_path) + os.sep + i['metadata_path']
        f = open(s, encoding="utf8")
        d = json.load(f)
        documents = []
        ids = []
        metadatas = []
        for j in d:
            documents.append(j['detail_desc'])
            ids.append(str(j['article_id']))
            metadatas.append(j)
        p = server_base_path / i['fclip_path']
        with open(p, 'rb') as c:
            image_embeddings = pickle.load(c)
        embeddings = image_embeddings.tolist()
        document_indices = list(range(len(documents)))
        num_batches = len(batched(document_indices, 41666))
        current_batch = 1
        for batch in batched(document_indices, 41666):  # maximum batch size 41666
            print(f"Processing batch {current_batch + 1}/{num_batches}")
            start_idx = batch[0]
            end_idx = batch[-1]
            collection.add(
                ids=ids[start_idx:end_idx],
                embeddings=embeddings[start_idx:end_idx],
                metadatas=metadatas[start_idx:end_idx],
                documents=documents[start_idx:end_idx]
            )
            current_batch += 1
    print("ChromaDB update completed.")


def get_num_collection():
    return len(chroma_client.list_collections())


def get_collection_from_index(i):
    for col in chroma_client.list_collections():
        if col.metadata['id'] == i:
            return col


def get_collection_id_from_name(name):
    for col in chroma_client.list_collections():
        if col.name == name:
            return col.metadata['id']


def get_collections():
    col_name = []
    for col in chroma_client.list_collections():
        i = col.metadata['id']
        row = [i, col.name]
        col_name.append(row)
    return sorted(col_name, key=lambda x: x[1])


def get_random_images(n_range):
    images = []
    for i in range(0, n_range):
        row = []
        random_c = random.sample(range(get_num_collection()), 1)
        random_c = random_c[0] + 1
        col = get_collection_from_index(random_c)
        n_col = col.count()
        r = random.sample(range(n_col), 1)
        row.append(random_c)
        row.append(col.peek(limit=n_col)['metadatas'][r[0]]['article_id'])
        images.append(row)
    return images


def is_load():
    try:
        if chroma_client is None:
            return False
        else:
            return True
    except:
        return False


def get_url(root: str, name: str):
    return str(server_base_path) + os.sep + str(root) + os.sep + name + ".jpg"


def get_dress_info(image_name: str, collection_id: int):
    col = get_collection_from_index(collection_id)
    param = []
    metadata = col.get(ids=[image_name]).get('metadatas', [])
    if metadata:
        char = metadata[0]
        param.append(char.get('prod_name'))  # C
        param.append(char.get('detail_desc'))
        param.append(char.get('product_type_name'))  # E
        param.append(char.get('product_group_name'))  # F
        param.append(char.get('colour_group_name'))
        param.append(col.name)  # H
    return param


def get_representative_image(col):
    if not col.metadata["representative"] == "":
        rep = col.metadata["representative"]
    else:
        n_col = col.count()
        r = random.sample(range(n_col), 1)
        rep = col.peek(limit=n_col)['metadatas'][r[0]]['article_id']
    return rep


def get_collection_for_modify():
    cs = []
    i = 0
    for col in chroma_client.list_collections():
        i = i + 1
        row = [col.name, i, get_representative_image(col)]
        cs.append(row)
    return cs


def get_image_from_collection(id_col: int):
    col = get_collection_from_index(id_col)
    n_col = col.count()
    peek = col.peek(limit=n_col)['metadatas']
    return peek, n_col, col.name


def retrieval_from_text(text: str, col_id: str):
    im = []
    n_results = os.getenv('N_OF_RESULTS', 10)
    if col_id == "all":
        for collection in chroma_client.list_collections():
            index = get_collection_id_from_name(collection.name)
            t = [text]
            text_vector = fclip.encode_text(t, batch_size=8)
            r = collection.query(query_embeddings=text_vector.tolist(), n_results=int(n_results))
            row = [[index] * len(r['ids'][0]), [collection.name] * len(r['ids'][0]), r['ids'][0], r['distances'][0]]
            im.append(row)
    else:
        collection = get_collection_from_index(int(col_id))
        t = [text]
        text_vector = fclip.encode_text(t, batch_size=8)
        r = collection.query(query_embeddings=text_vector.tolist(), n_results=int(n_results))
        row = [[col_id] * len(r['ids'][0]), [collection.name] * len(r['ids'][0]), r['ids'][0], r['distances'][0]]
        im.append(row)
    return sorted(im, key=lambda x: x[1])


def retrieval_from_image(img, col_id: str):
    im = []
    n_results = os.getenv('N_OF_RESULTS', 10)
    if col_id == "all":
        for collection in chroma_client.list_collections():
            index = get_collection_id_from_name(collection.name)
            t = [img]
            image_vector = fclip.encode_images(t, batch_size=8)
            r = collection.query(query_embeddings=image_vector.tolist(), n_results=int(n_results))
            row = [[index] * len(r['ids'][0]), [collection.name] * len(r['ids'][0]), r['ids'][0], r['distances'][0]]
            im.append(row)
    else:
        collection = get_collection_from_index(int(col_id))
        t = [img]
        image_vector = fclip.encode_images(t, batch_size=8)
        r = collection.query(query_embeddings=image_vector.tolist(), n_results=int(n_results))
        row = [[col_id] * len(r['ids'][0]), [collection.name] * len(r['ids'][0]), r['ids'][0], r['distances'][0]]
        im.append(row)
    return sorted(im, key=lambda x: x[1])


def get_len_of_collection():
    f = open(dataset_root / 'dataset.json')
    data = json.load(f)
    f.close()
    return len(data)


def embedding_image(image_list, path):
    fclip = FashionCLIP('fashion-clip')
    images_embedded = fclip.encode_images(image_list, batch_size=8)
    with open(path, 'wb+') as f:
        pickle.dump(images_embedded, f)


def set_dataset_json(name, rep):
    if rep == "None":
        rep = ""
    else:
        rep = rep.split(".")
        rep = rep[0]
    f = open(dataset_root / 'dataset.json')
    data = json.load(f)
    f.close()
    id_col = len(data) + 1
    n = "f_clip_" + str(id_col) + ".pkl"
    fclip_path = str(dataset_root) + os.sep + "Fclip" + os.sep + "f_clip_" + str(id_col) + ".pkl"
    fclip_path_url = "dataset" + os.sep + "Fclip" + os.sep + n
    n = "collection_" + str(id_col) + ".json"
    json_path = "dataset" + os.sep + "Metadata" + os.sep + n
    n = "collection_" + str(id_col)
    image_path = "dataset" + os.sep + "Images" + os.sep + n
    row = {
        "collection": id_col,
        "image_path": str(image_path),
        "metadata_path": str(json_path),
        "fclip_path": str(fclip_path_url),
        "name": name,
        "representative": rep
    }
    data.append(row)
    with open(dataset_root / 'dataset.json', 'w') as outfile:
        json.dump(data, outfile)
    return fclip_path


def delete_col(id_col):
    n = "f_clip_" + str(id_col) + ".pkl"
    fclip_path = "dataset" + os.sep + "Fclip" + os.sep + n
    n = "collection_" + str(id_col) + ".json"
    json_path = "dataset" + os.sep + "Metadata" + os.sep + n
    n = "collection_" + str(id_col)
    image_path = "dataset" + os.sep + "Images" + os.sep + n
    os.remove(server_base_path / fclip_path)
    os.remove(server_base_path / json_path)
    shutil.rmtree(server_base_path / image_path)
    f = open(dataset_root / 'dataset.json')
    data = json.load(f)
    f.close()
    n = 1
    new_data = []
    for d in data:
        if int(d['collection']) < int(id_col):
            new_data.append(d)
            n = n + 1
        if int(d['collection']) > int(id_col):
            a = "f_clip_" + str(d['collection']) + ".pkl"
            fclip_path = "dataset" + os.sep + "Fclip" + os.sep + a
            a = "collection_" + str(d['collection']) + ".json"
            json_path = "dataset" + os.sep + "Metadata" + os.sep + a
            a = "collection_" + str(d['collection'])
            image_path = "dataset" + os.sep + "Images" + os.sep + a
            a = "f_clip_" + str(n) + ".pkl"
            new_fclip_path = "dataset" + os.sep + "Fclip" + os.sep + a
            a = "collection_" + str(n) + ".json"
            new_json_path = "dataset" + os.sep + "Metadata" + os.sep + a
            a = "collection_" + str(n)
            new_image_path = "dataset" + os.sep + "Images" + os.sep + a
            os.rename(server_base_path / image_path, server_base_path / new_image_path)
            os.rename(server_base_path / json_path, server_base_path / new_json_path)
            os.rename(server_base_path / fclip_path, server_base_path / new_fclip_path)
            d['collection'] = n
            d['image_path'] = new_image_path
            d['metadata_path'] = new_json_path
            d['fclip_path'] = new_fclip_path
            new_data.append(d)
            n = n + 1
    with open(dataset_root / 'dataset.json', 'w') as outfile:
        json.dump(new_data, outfile)


class TargetPad:
    def __init__(self, target_ratio: float, size: int, pad_value: Optional[int] = 0):
        self.size = size
        self.target_ratio = target_ratio
        self.pad_value = pad_value

    def __call__(self, image):
        w, h = image.size
        actual_ratio = max(w, h) / min(w, h)
        if actual_ratio < self.target_ratio:  # check if the ratio is above or below the target ratio
            return image
        scaled_max_wh = max(w, h) / self.target_ratio  # rescale the pad to match the target ratio
        hp = max(int((scaled_max_wh - w) / 2), 0)
        vp = max(int((scaled_max_wh - h) / 2), 0)
        padding = [hp, vp, hp, vp]
        return F.pad(image, padding, self.pad_value, 'constant')


def targetpad_resize(target_ratio: float, dim: int, pad_value: int):
    return Compose([
        TargetPad(target_ratio, dim, pad_value),
        Resize(dim, interpolation=PIL.Image.BICUBIC),
        CenterCrop(dim),
    ])
