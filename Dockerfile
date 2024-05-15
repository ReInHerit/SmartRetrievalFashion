FROM python:3.11
WORKDIR .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python download_fashion_clip_model.py  # to pre-download the model and speed up the next command
#CMD [ "flask", "run","--host","0.0.0.0","--port","5000"]
# The port is picked from the environment variable PORT.
# Must use shell form of CMD to use environment variables
CMD gunicorn --bind :${PORT} app:app