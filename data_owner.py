from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify
import requests
import warnings
import numpy as np
import phe as paillier
from sonar.contracts import ModelRepository,Model
from syft.he.paillier.keys import KeyPair
from syft.nn.linear import LinearClassifier
from sklearn.datasets import load_diabetes
import os
import pickle
import pandas as pd

app = Flask(__name__)

PUBLIC_KEY = 1

NOTIFY_URL = 'http://localhost:5556/notify'
MODELS_URL = 'http://localhost:5556/models'

CONTRACT_ADDRESS = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
PORT = 9545
HOST = 'localhost'

UPLOAD_FOLDER = 'uploads'

REPO = ModelRepository(contract_address = CONTRACT_ADDRESS,
    web3_port = PORT, web3_host = HOST)

def get_balance(account):
    return REPO.web3.fromWei(REPO.web3.eth.getBalance(account),'ether')

def update_balance_data(account):

    fname = 'balances_{}.pkl'.format(account)

    try:
        with open(fname,'rb') as f:
            balances = pickle.load(f)
    except FileNotFoundError:
        balances = []

    balances.append(get_balance(account))

    with open(fname,'wb') as f:
        balances = pickle.load(f)

    return balances

@app.route('/dashboard', methods=['POST'])
def share_data():
    model_id = int(request.form.get('model_id'))
    data_owner_address = request.form.get('data_owner_address')
    input_data = request.files['input_data']
    target_data = request.files['target_data']
    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')
    input_data.save(input_path)
    target_data.save(target_path)
    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values

    balances = update_balance_data(data_owner_address)

    model = REPO[model_id].submit_gradient(data_owner_address, input_data, target_data)
    
    return 'Done'

@app.route('/dashboard')
def get_results():
    data_owner_address = request.form.get('data_owner_address')
    num_models = REPO.call.getNumModels()
    models = {}

    for model_id in range(num_models):
        models[model_id] = REPO.call.getModel(model_id)[0]
    balances = update_balance_data(data_owner_address)

    return jsonify({'balances':balances,
                    'models':models})

app.debug = True
app.run(port=5557, host='0.0.0.0')
