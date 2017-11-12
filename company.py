from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify
import pandas as pd
import time
import warnings
import numpy as np
import phe as paillier
from sonar.contracts import ModelRepository,Model
from syft.he.paillier.keys import KeyPair
from syft.nn.linear import LinearClassifier
from sklearn.datasets import load_diabetes
from threading import Thread
import os

app = Flask(__name__)

warnings.filterwarnings('ignore')

UPLOAD_FOLDER = 'uploads'

ADDRESS = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
PORT = 9545
HOST = 'localhost'

REPO = ModelRepository(contract_address = ADDRESS,
web3_port = PORT, web3_host = HOST)

CLASSIFIERS = {'Linear_Classifier': LinearClassifier}
names = {}
num_gradients = {0:0}
errors = {}
data = {}
address = 1
pubkey,prikey = KeyPair().generate(n_length=1024)
company_owner ='0xf17f52151ebef6c7334fad080c5704d77216b732'

def get_gradients(model_id):
    num_grads_old = num_gradients[model_id]
    num_grads_new =  REPO.call.getNumGradientsforModel(model_id)
    grads = []
    if num_grads_new - num_grads_old > 0:
        num_gradients[model_id] = num_grads_new
        #Since id is incremented from 0
        for grad_id in range(num_grads_old, num_grads_new):
            grads.append(REPO[model_id][grad_id])
    return grads

def evaluate_gradients(model_id):
    grads = get_gradients(model_id)
    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')
    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values
    if len(grads):
        for grad in grads:
            new_error = REPO[model_id].evaluate_gradient(company_owner,grad,prikey,pubkey,input_data,target_data)
            errors[model_id].append(new_error)

# def manage_gradients():
#     while True:
#         time.sleep(1)
#         num_models = REPO.call.getNumModels()
#         for model_id in range(num_models):
#             evaluate_gradients(model_id)

# thread = Thread(target=manage_gradients)
# thread.start()

def get_balance(account):
    return REPO.web3.fromWei(REPO.web3.eth.getBalance(account),'ether')

@app.route('/models')
def get_model_details():
    return jsonify(names)

@app.route('/notify')
def notify():
    model_id = int(request.args.get('model_id'))
    print('model_id', model_id)
    if model_id is not None:
        evaluate_gradients(model_id)
    return "done"

@app.route('/add_model',methods=['POST'])
def add_model():
    bounty = request.form.get('bounty')
    target_error = request.form.get('target_error')
    clf_name = request.form.get('clf_name')
    model_name = request.form.get('model_name')

    input_data = request.files['input_data']
    target_data = request.files['target_data']

    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')

    input_data.save(input_path)
    target_data.save(target_path)

    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values

    # input_data = request.form.get('input_data').split('\n')
    # target_data = request.form.get('target_data').split('\n')

    # input_data = np.array([list(map(float, i.split(','))) for i in input_data])
    # target_data = np.array([list(map(float, i.split(','))) for i in target_data])

    clf = CLASSIFIERS[clf_name](desc=model_name,
                                n_inputs=input_data.shape[1],
                                n_labels=target_data.shape[1])
    initial_error = clf.evaluate(input_data, target_data)
    clf.encrypt(pubkey)
    model = Model(owner=company_owner,
                syft_obj = clf,
                bounty = int(bounty),
                initial_error = initial_error,
                target_error = int(target_error)
                )
    model_id = REPO.submit_model(model)
    num_gradients[model_id] = 0
    errors[model_id] = []
    names[model_id] = model_name

    data[model_id] = {}
    data[model_id]['input'] = input_data
    data[model_id]['target'] = target_data
    return jsonify({'model_name':model_name})

@app.route('/dashboard')
def get_model_data():
    data = {'model_names':names}
    model_id = request.args.get('model_id')
    if model_id is not None:
        data.update(dict(num_grads=num_gradients[model_id], errors=errors[model_id]))
    return jsonify(data)

app.debug = True
app.run(port=5556, host='0.0.0.0')
