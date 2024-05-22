from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os
import base64
import io
from celery import Celery
from PIL import Image
from tasks import apply_grayscale_filter, prepare_image_for_task

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TRANSFORMED_FOLDER'] = 'transformed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload and transformed directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TRANSFORMED_FOLDER'], exist_ok=True)

# Celery configuration
celery = Celery(app.name, broker='pyamqp://erick:erick@3.137.151.50//', backend='rpc://')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        image_data = prepare_image_for_task(file_path)
        result = apply_grayscale_filter.delay(image_data)
        grayscale_image_data = result.get()
        grayscale_image_bytes = base64.b64decode(grayscale_image_data)
        
        transformed_filename = 'grayscale_' + filename
        transformed_path = os.path.join(app.config['TRANSFORMED_FOLDER'], transformed_filename)
        with open(transformed_path, "wb") as image_file:
            image_file.write(grayscale_image_bytes)
        
        return redirect(url_for('uploaded_file', filename=transformed_filename))
    return redirect(request.url)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['TRANSFORMED_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
