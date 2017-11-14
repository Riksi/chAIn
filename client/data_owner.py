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
import json
from decimal import Decimal

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

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def get_balance(account):
    return REPO.web3.fromWei(REPO.web3.eth.getBalance(account),'ether')

def update_balance_data(account):

    fname = 'balances_{}.pkl'.format(account)

    try:
        with open(fname,'rb') as f:
            balances = pickle.load(f)

    except FileNotFoundError:
        balances = []

    old_balance = balances[-1] if len(balances) else None
    new_balance = get_balance(account)

    if old_balance is None or (old_balance != new_balance):
        balances.append(new_balance)

    with open(fname,'wb') as f:
        pickle.dump(balances, f)

    return balances

@app.route('/dashboard', methods=['POST'])
def share_data():
    model_id = int(request.form.get('model_id'))
    data_owner_address = request.form.get('data_owner_address')
    input_data = request.files['input_data']
    target_data = request.files['target_data']
    input_path = os.path.join(UPLOAD_FOLDER, 'input_data')
    target_path = os.path.join(UPLOAD_FOLDER, 'target_data')

    print('model_id', model_id)
    print('data_owner_address', data_owner_address)

    input_data.save(input_path)
    target_data.save(target_path)
    input_data = pd.read_csv(input_path).values
    target_data = pd.read_csv(target_path).values

    print('input shape', input_data.shape  )
    print('target shape', target_data.shape  )
    balances = update_balance_data(data_owner_address)

    model = REPO[model_id].submit_gradient(data_owner_address, input_data[1,:], target_data[1,:])

    return 'Done'

@app.route('/dashboard')
def get_results():
    data_owner_address = request.args.get('data_owner_address')
    num_models = REPO.call.getNumModels()
    models = {}

    for model_id in range(num_models):
        model_id_name,_,_,_,_,_ = REPO.call.getModel(model_id)
        models[model_id] = model_id_name.replace('\u0000', "")
    balances = update_balance_data(data_owner_address)
    return json.dumps({'balances':balances, 'models':models}, cls=DecimalEncoder)

app.debug = True
app.run(port=5557, host='0.0.0.0')
