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
import pandas as pd

app = Flask(__name__)

balances = []

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

@app.route('/dashboard', methods=['POST'])
def share_data():
    balances.append(get_balance(PUBLIC_KEY))
    model_id = int(request.form.get('model_id'))
    print('model_id', model_id)
    data_owner_address = request.form.get('data_owner_address')
    input_data = request.files['input_data']
    target_data = request.files['target_data']

    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')

    input_data.save(input_path)
    target_data.save(target_path)

    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values

    model = REPO[model_id]

    model.submit_gradient(data_owner_address,input_data[0],target_data[0])
    requests.get(NOTIFY_URL, params={'model_id':model_id})
    balances.append(get_balance(PUBLIC_KEY))
    return jsonify({'balances':balances})

@app.route('/dashboard')
def get_results():
    models = requests.get(MODELS_URL).json()
    return jsonify({'balances':balances,
                    'models':models})

app.debug = True
app.run(port=5557, host='0.0.0.0')
