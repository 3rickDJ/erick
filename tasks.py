import base64
import io
from celery import Celery
from PIL import Image

app = Celery('tasks', broker='pyamqp://erick:erick@3.137.151.50//', backend='rpc://')

@app.task
def add(x, y):
    return x + y

@app.task
def apply_grayscale_filter(image_data):
    # Decode the base64 string to bytes
    image_bytes = base64.b64decode(image_data)
    # Convert bytes to a PIL image
    image = Image.open(io.BytesIO(image_bytes))
    # Apply the grayscale filter
    grayscale_image = image.convert('L')
    # Convert the grayscale image back to bytes
    buffered = io.BytesIO()
    grayscale_image.save(buffered, format="PNG")
    grayscale_image_bytes = buffered.getvalue()
    # Encode the bytes to a base64 string
    grayscale_image_data = base64.b64encode(grayscale_image_bytes).decode('utf-8')
    return grayscale_image_data

def prepare_image_for_task(image_path):
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
    image_data = base64.b64encode(image_bytes).decode('utf-8')
    return image_data

def process_image(image_path):
    image_data = prepare_image_for_task(image_path)
    result = apply_grayscale_filter.delay(image_data)
    image = result.get()
    with open("grayscale_" + image_path, "wb") as image_file:
        image_file.write(base64.b64decode(image))
    return image

# Example usage
if __name__ == "__main__":
    image_path = "pacman.png"
    image_data = prepare_image_for_task(image_path)
    result = apply_grayscale_filter.delay(image_data)
    image = result.get()
    with open("grayscale_pacman.png", "wb") as image_file:
        image_file.write(base64.b64decode(image))
    print(result.get())  # This will print the base64 string of the grayscale image
