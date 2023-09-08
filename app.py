from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
import os
import json
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import interactive
from torch import nn
from PIL import Image
from collections import OrderedDict
from torchvision import datasets, transforms, models
import time
import uuid

app = Flask(__name__)

# Configure a folder where uploaded files will be stored
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set the default values if needed
top_k = 5
device = "cpu"
category_names = None

# Load the category names
if category_names is None:
    with open('cat_to_name.json', 'r') as f:
        cat_to_name = json.load(f)
else:
    filename, file_extension = os.path.splitext(category_names)
    if file_extension != '.json':
        print("Please use file extension .json instead of " + category_names + ".")
        exit()
    else:
        with open(category_names, 'r') as f:
            cat_to_name = json.load(f)
    
# Write a function that loads a checkpoint and rebuilds the model
def loading_model(checkpoint_path):
    
    check_path = torch.load(checkpoint_path)
    # add for test
    arch = "vgg13"
    
    if (arch == 'vgg13'):
        model = models.vgg13(pretrained=True)
        input_size = 25088
        hidden_units = 4096
        output_size = 102
    elif (arch == 'densenet121'):
        model = models.densenet121(pretrained=True)
        input_size = 1024
        hidden_units = 500
        output_size = 102
            
    for param in model.parameters():
        param.requires_grad = False
    
    model.class_to_idx = check_path['class_to_idx']
                    
    classifier = nn.Sequential(OrderedDict([('fc1', nn.Linear(input_size, hidden_units)),
                                            ('relu', nn.ReLU()),
                                            ('dropout1',nn.Dropout(0.2)),
                                            ('fc2', nn.Linear(hidden_units, output_size)),
                                            ('output', nn.LogSoftmax(dim=1))]))
    
    # Put the classifier on the pretrained network
    model.classifier = classifier
    model.load_state_dict(check_path['state_dict'])
    ####print("The model is loaded to" + save_dir)
    return model

model = loading_model('model_data/save_checkpoint.pth')

def process_image(image):
    ''' Scales, crops, and normalizes a PIL image for a PyTorch model,
        returns an Numpy array
    '''
    
    # Process a PIL image for use in a PyTorch model
    pil_image = Image.open(image)
    
    # Edit
    edit_image = transforms.Compose([transforms.Resize(256),
                                     transforms.RandomCrop(224),
                                     transforms.ToTensor(),
                                     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
    
    # Dimension
    img_tensor = edit_image(pil_image)
    processed_image = np.array(img_tensor)
    processed_image = processed_image.transpose((0, 2, 1))
    
    return processed_image

def imshow(image, ax=None, title=None):
    if ax is None:
        fig, ax = plt.subplots()
    if title:
        plt.title(title)

    image = image.transpose((1, 2, 0))
    
    # Undo preprocessing
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image = std * image + mean
    
    # Image needs to be clipped between 0 and 1 or it looks like noise when displayed
    image = np.clip(image, 0, 1)
        
    return ax

def predict(image_path, model, topk = top_k):
    ''' Predict the class (or classes) of an image using a trained deep learning model.
    '''
    
    # Implement the code to predict the class from an image file
    model.to(device)
    img_torch = process_image(image_path)
    img_torch = torch.from_numpy(img_torch).type(torch.FloatTensor)
    img_torch = img_torch.unsqueeze(0)
    img_torch = img_torch.float()
    
    with torch.no_grad():
        if device == "cpu":
            output = model.forward(img_torch.cpu())
        elif device == "cuda":
            output = model.forward(img_torch.cuda())
   
    probability = F.softmax(output.data,dim=1)
    probabilies = probability.topk(topk)
    score = np.array(probabilies[0][0])
    index = 1
    flowers_list = [cat_to_name[str(index + 1)] for index in np.array(probabilies[1][0])]
   
    return score, flowers_list

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

@app.route('/', methods=['GET'])
def display_form():
    # Render the HTML form for image upload
    return render_template('index.html')

@app.route('/', methods=['POST'])
def classify_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        # Generate a unique filename based on timestamp and uuid
        unique_filename = f"{int(time.time())}_{str(uuid.uuid4())[:8]}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Perform image classification
        score, flower_list = predict(file_path, model)
        probability = np.exp(score).tolist()
        probability_rounded = [round(p, 5) for p in probability]
        
        # Pass the filename without the path
        filename = unique_filename

        zipped_data = list(zip(flower_list, probability_rounded))

        # Return JSON response
        response_data = {
            'image_name': filename,
            'zipped_data': zipped_data
        }
        return jsonify(response_data)

    return jsonify({'error': 'Invalid file format'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))