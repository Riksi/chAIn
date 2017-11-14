from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify
import pandas as pd
import time
import warnings
import numpy as np
import pickle
import pandas as pd
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

COMPANY_ADDRESS ='0xf17f52151ebef6c7334fad080c5704d77216b732'

REPO = ModelRepository(contract_address = ADDRESS,
web3_port = PORT, web3_host = HOST)

CLASSIFIERS = {'Linear_Classifier': LinearClassifier}

with open('keys.pkl','rb') as f:
    PUBLIC_KEY,PRIVATE_KEY = pickle.load(f)

def get_gradients(model_id, num_grads_old):
    num_grads_new =  REPO.call.getNumGradientsforModel(model_id)
    grads = []
    if num_grads_new - num_grads_old > 0:
        #Since id is incremented from 0
        for grad_id in range(num_grads_old, num_grads_new):
            grads.append(REPO[model_id][grad_id])
    return grads, num_grads_new

def evaluate_gradients(model_id):
    with open ('model_{}.pkl'.format(model_id), 'rb') as f:
        model_name, num_gradients, errors = pickle.load(f)

    grads, num_gradients = get_gradients(model_id, num_gradients)
    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')
    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values

    if len(grads):
        for grad in grads:
            new_error = REPO[model_id].evaluate_gradient(COMPANY_ADDRESS,grad,
                PRIVATE_KEY,PUBLIC_KEY,input_data,target_data)

            errors.append(new_error/10000000000)
    save_model_data(model_id, model_name, num_gradients, errors)

def manage_gradients():
    while True:
        time.sleep(1)
        num_models = REPO.call.getNumModels()
        for model_id in range(num_models):
            evaluate_gradients(model_id)

thread = Thread(target=manage_gradients)
thread.start()

def save_model_data(model_id, model_name, num_gradients, errors):
    with open ('model_{}.pkl'.format(model_id), 'wb') as f:
        pickle.dump((model_name, num_gradients, errors), f)

def get_balance(account):
    return REPO.web3.fromWei(REPO.web3.eth.getBalance(account),'ether')

# @app.route('/models')
# def get_model_details():
#     return jsonify(names)

# @app.route('/notify')
# def notify():
#     model_id = int(request.args.get('model_id'))
#     print('model_id', model_id)
#     if model_id is not None:
#         evaluate_gradients(model_id)
#     return "done"

@app.route('/add_model',methods=['POST'])
def add_model():
    bounty = request.form.get('bounty')
    target_error = request.form.get('target_error')
    clf_name = request.form.get('clf_name')
    model_name = request.form.get('model_name')

    print('bounty', bounty)
    print('target_error', target_error)
    print('clf_name', clf_name)
    print('model_name', model_name)

    input_data = request.files['input_data']
    target_data = request.files['target_data']

    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')

    input_data.save(input_path)
    target_data.save(target_path)
    print('saved')

    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values

    clf = CLASSIFIERS[clf_name](desc=model_name,
                                n_inputs=input_data.shape[1],
                                n_labels=target_data.shape[1])
    initial_error = clf.evaluate(input_data, target_data)

    clf.encrypt(PUBLIC_KEY)
    model = Model(name = model_name.strip(),
                owner=COMPANY_ADDRESS.strip(),
                syft_obj = clf,
                bounty = int(bounty.strip()),
                initial_error = initial_error,
                target_error = int(target_error.strip())
                )
    model_id = REPO.submit_model(model)

    num_gradients = 0
    errors = []

    save_model_data(model_id, model_name, num_gradients, errors)

    return jsonify({'model_name':model_name})

@app.route('/models')
def get_model_data():
    num_models = REPO.call.getNumModels()
    names = {}
    errors = {}
    num_gradients = {}
    for model_id in range(num_models):
        model_id_name,_,_,_,_,_ = REPO.call.getModel(model_id)
        names[model_id] = model_id_name.replace('\u0000', "")
        with open ('model_{}.pkl'.format(model_id), 'rb') as f:
            model_name, num_grads, errs = pickle.load(f)
        errors[model_id] = [e/10000000000000000000000000000000000 for e in errs]
        print('errors', errors[model_id])
        num_gradients[model_id] = num_grads
    return jsonify(dict(names=names, num_gradients=num_gradients, errors=errors))

app.debug = True
app.run(port=5556, host='0.0.0.0')
