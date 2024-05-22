from celery import Celery
from PIL import Image

app = Celery('tasks', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y

@app.task
def apply_grayscale_filter(imageObject):
    image = imageObject.convert('L')
    return image