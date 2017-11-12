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

app = Flask(__name__)

balances = []

PUBLIC_KEY = 1

NOTIFY_URL = 'nfy'
MODELS_URL = 'mdl'

CONTRACT_ADDRESS = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
PORT = 9545
HOST = 'localhost'

REPO = ModelRepository(contract_address = CONTRACT_ADDRESS, web3_port = PORT, web3_host = HOST)

def get_balance(account):
    return REPO.web3.fromWei(REPO.web3.eth.getBalance(account),'ether')

@app.route('/dashboard', methods=['POST'])
def share_data():
    balances.append(get_balance(PUBLIC_KEY))
    address = request.form.get('address')
    model_id = request.form.get('model_id')
    input_data = request.form.get('input_data')
    target_data = request.form.get('target_data')
    model = REPO[model_id]
    model.submit_gradient(address,input_data,target_data)
    balances.append(get_balance(PUBLIC_KEY))
    return jsonify({'balances':balances})

@app.route('/dashboard')
def get_results():
    models = requests.get(MODELS_URL).json()
    return jsonify({'balances':balances, 'models':models})

app.debug = True
app.run(port=5555, host='0.0.0.0')