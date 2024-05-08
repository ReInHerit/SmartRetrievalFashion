FROM python:3.11
WORKDIR .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python download_fashion_clip_model.py  # to pre-download the model and speed up the next command
#CMD [ "flask", "run","--host","0.0.0.0","--port","5000"]
CMD ["gunicorn", "--bind", ":5000", "app:app"]