import json
import math
import os
import random
import data_utilis
import PIL.Image
import shutil
from dotenv import load_dotenv

from flask import Flask, render_template, send_file, request, url_for, redirect
from io import BytesIO
from data_utilis import *
from data_utilis import targetpad_resize

# Load the .env file
load_dotenv()
port = int(os.environ.get("PORT", 5000))

app = Flask(__name__)
upload = image_root
app.config['UPLOAD'] = upload
app.config['UPLOAD_TEMP'] = server_base_path / "static" / "Image" / "temporary_file"


@app.route('/')
@app.route('/home')
def home():
    load()
    if not data_utilis.is_load() or data_utilis.get_num_collection() == 0:
        update_chroma()
    images = get_random_images(6)
    return render_template('base.html', names=images, active="Home", cols=get_collections())


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def search():
    if not is_load():
        load()
    if request.method == 'POST':
        search = request.form['search']
        collection = request.form['collection']
        image = request.files['image']
        if not search == "":
            imgs = retrieval_from_text(search, collection)
            return render_template('result.html', imgs=imgs, search=search, cols=get_collections())
        else:
            img = PIL.Image.open(image)
            imgs = retrieval_from_image(img.convert('RGB'), collection)
            return render_template('result.html', imgs=imgs, search="", cols=get_collections())


@app.route('/search_similar/<string:image_name>/<int:collection>/<par>')
def search_similar(image_name: str, collection: str, par):
    if not is_load():
        load()
    path_image = str(image_root) + os.sep + "collection_" + str(collection) + os.sep + image_name + ".jpg"
    img = PIL.Image.open(path_image)
    imgs = retrieval_from_image(img.convert('RGB'), par)
    return render_template('result.html', imgs=imgs, search="", cols=get_collections())


@app.route('/get_image/<string:image_name>/<int:collection>')
@app.route('/get_image/<string:image_name>/<int:collection>/<int:dim>')
def get_image(image_name: str, collection: str, dim: Optional[int] = None):
    if not is_load():
        load()
    print("get_image", image_name, collection, dim)
    path_image = str(image_root) + os.sep + "collection_" + str(collection) + os.sep + image_name + ".jpg"
    if dim:
        transform = targetpad_resize(1.25, int(dim), 255)
        pil_image = transform(PIL.Image.open(path_image))
    else:
        pil_image = PIL.Image.open(path_image)
    img_io = BytesIO()
    pil_image.save(img_io, 'JPEG', quality=80)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


@app.route('/char_image/<string:image_name>/<string:collection>')
def char_image(image_name: str, collection: str):
    if not is_load():
        load()
    param = get_dress_info(image_name, int(collection))
    return render_template('feature.html', id=image_name, collection=collection, param=param,
                           cols=get_collections(), search_similar=True)


@app.route('/add/')
def add():
    return render_template('add_collection.html', page=1)


@app.route('/add/', methods=['GET', 'POST'])
def add_post():
    global i
    global col_name
    global rep
    names = []
    images = []
    len = 0
    if request.method == 'POST':
        col_name = request.form['name']
        i = request.files.getlist("image")
        rep = request.form['rep']
        for j in i:
            len = len + 1
            names.append(j.filename)
            j.save(os.path.join(app.config['UPLOAD_TEMP'], j.filename))
            path = "Image/temporary_file/" + j.filename
            images.append(path)
    return render_template('add_collection.html', page=2, names=names, image=images, len=len)


@app.route('/modify')
def modify():
    if not is_load():
        load()
    if not data_utilis.is_load() or data_utilis.get_num_collection() == 0:
        update_chroma()
    cs = get_collection_for_modify()
    # alphabetical order
    cs_sorted = sorted(cs, key=lambda x: x[0])
    return render_template('modify.html', active="Modify", collections=cs_sorted, cols=get_collections())


@app.route('/collection/<col>')
@app.route('/collection/<col>/<page>')
def collection(col, page: Optional[int] = 1, operation: Optional[str] = "s"):
    n = 18
    if not is_load():
        load()
    catalog, n_col, col_name = get_image_from_collection(int(col))
    if n_col < n:
        n = n_col
    n_page = n_col / n
    n_page = str(int(n_page))
    if str(page) == n_page:
        ls = int(n_col)
    else:
        ls = int(page) * n + n
    li = int(page) * n - n
    page_p = int(page) - 1
    page_n = int(page) + 1
    return render_template('modify_collection.html', active="Modify", l_i=li, l_s=ls, n_page=int(n_page),
                           catalog=catalog, n_col=n_col, c_id=col, page=int(page), page_n=page_n, page_p=page_p,
                           col_name=col_name)


@app.route('/load', methods=['GET', 'POST'])
def load_collection():
    n = get_len_of_collection() + 1
    par = []
    images = []
    if request.method == 'POST':
        cn = col_name.split(" ")
        c_name = ""
        for c in cn:
            c_name = c_name + c
        path = str(image_root) + os.sep + "collection_" + str(n)
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            shutil.rmtree(path)
            os.makedirs(path)
        for j in i:
            name = request.form["name" + j.filename]
            description = request.form["description" + j.filename]
            product_type = request.form["type" + j.filename]
            group = request.form["group" + j.filename]
            colour = request.form["colour" + j.filename]
            image_id = j.filename.split(".")
            row = {
                "article_id": image_id[0],
                "prod_name": name,
                "product_type_name": product_type,
                "product_group_name": group,
                "colour_group_name": colour,
                "detail_desc": description
            }
            par.append(row)
            shutil.move(server_base_path / "static" / "Image" / "temporary_file" / j.filename, path)
            images.append(path + os.sep + str(j.filename))
        json_path = str(data_utilis.metadata_path) + os.sep + "collection_" + str(n) + ".json"
        with open(json_path, 'w') as outfile:
            json.dump(par, outfile)
        fclip_path = data_utilis.set_dataset_json(c_name, rep)
        data_utilis.embedding_image(images, fclip_path)
    update_chroma()
    return redirect(url_for('home'))


@app.route('/delete_collection/<col>')
def delete_collection(col):
    if not is_load():
        load()
    data_utilis.delete_col(col)
    update_chroma()
    return redirect(url_for('home'))


@app.route('/add_image_at_collection', methods=['GET', 'POST'])
def add_image_at_collection():
    global i
    global col_id
    names = []
    images = []
    len = 0
    path = str(server_base_path) + os.sep + "static" + os.sep + "Image" + os.sep + "temporary_file"
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        shutil.rmtree(path)
        os.makedirs(path)
    if request.method == 'POST':
        col_id = request.form['name']
        i = request.files.getlist("image")
        for j in i:
            len = len + 1
            names.append(j.filename)
            j.save(os.path.join(app.config['UPLOAD_TEMP'], j.filename))
            path = "Image" + os.sep + "temporary_file" + os.sep + j.filename
            images.append(path)
    return render_template('add_metadata.html', names=names, image=images, len=len)


@app.route('/load_image', methods=['GET', 'POST'])
def load_image():
    if not is_load():
        load()
    images = []
    if request.method == 'POST':
        path = str(image_root) + os.sep + "collection_" + col_id
        collection = get_collection_from_index(int(col_id))
        par = collection.peek()['metadatas']
        for p in par:
            images.append(path + os.sep + str(p['article_id']) + ".jpg")
        for j in i:
            name = request.form["name" + j.filename]
            description = request.form["description" + j.filename]
            product_type = request.form["type" + j.filename]
            group = request.form["group" + j.filename]
            colour = request.form["colour" + j.filename]
            image_id = j.filename.split(".")
            row = {
                "article_id": image_id[0],
                "prod_name": name,
                "product_type_name": product_type,
                "product_group_name": group,
                "colour_group_name": colour,
                "detail_desc": description
            }
            par.append(row)
            shutil.move(server_base_path / "static" / "Image" / "temporary_file" / j.filename, path)
            images.append(path + os.sep + str(j.filename))
        json_path = str(data_utilis.metadata_path) + os.sep + "collection_" + str(col_id) + ".json"
        with open(json_path, 'w') as outfile:
            json.dump(par, outfile)
        n = "f_clip_" + str(col_id) + ".pkl"
        fclip_path = "dataset" + os.sep + "Fclip" + os.sep + n
        data_utilis.embedding_image(images, fclip_path)
    update_chroma()
    return redirect(url_for('home'))


@app.route('/delete_image/<col>/<image>')
def delete_image(col, image):
    if not is_load():
        load()
    json_path = str(metadata_path) + os.sep + "collection_" + str(col) + ".json"
    f_clip_path = str(dataset_root) + os.sep + "Fclip" + os.sep + "f_clip_" + str(col) + ".pkl"
    f = open(json_path)
    data = json.load(f)
    f.close()
    new_data = []
    images = []
    for d in data:
        if d['article_id'] == str(image):
            name = d['article_id'] + ".jpg"
            n = "collection_" + str(col)
            path_i = image_root / n / name
            os.remove(path_i)
        else:
            path_i = str(image_root) + os.sep + "collection_" + str(col) + os.sep + d['article_id'] + ".jpg"
            new_data.append(d)
            images.append(path_i)
    with open(json_path, 'w') as outfile:
        json.dump(new_data, outfile)
    data_utilis.embedding_image(images, f_clip_path)
    update_chroma()
    return redirect(url_for('collection', col=col))
