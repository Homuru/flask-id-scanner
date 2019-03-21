from __future__ import print_function
import argparse
import cv2
import os
import sys
import pytesseract
import numpy as np
import tensorflow as tf
import flask
from flask import Flask, request, redirect, url_for, flash, jsonify
from flask_cors import CORS,cross_origin
from main.tweak import getInformation
from main.getTextArea import textDetection
import json

# res = getInformation('data/demo/CC8/CC8.jpg')
# print(res)

# Obtain the flask app object
app = Flask(__name__, static_url_path="", static_folder="data")
CORS(app)


UPLOAD_FOLDER = 'data/demo'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_AS_ASCII'] = False



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def scan(filename):
    fileFolder = filename.split('.')[0]
    textDetection(fileFolder)
    print('data/res/' + fileFolder + '/' + filename)
    # sleep(10)
    result = getInformation('data/demo/' + fileFolder + '/' + filename)
    return result

# scan('CC1.jpg')

@app.route('/')
@cross_origin()
def index():
    return flask.render_template('index.html', has_result=False)

@app.route('/test', methods = ['GET'])
@cross_origin()
def testing():
    return "test"

@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            fileFolder = filename.split('.')[0]
            save_path = app.config['UPLOAD_FOLDER'] + '/' + fileFolder + '/'
            os.makedirs(save_path, exist_ok=True)
            file.save(os.path.join(
                save_path, filename))
            result = scan(filename)
            result.update({'src':'/demo/' + fileFolder + '/' + filename})
            # return flask.render_template('result.html', result=result)
            return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port ='9000')
