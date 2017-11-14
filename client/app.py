from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify

import warnings
import numpy as np
import phe as paillier
from sonar.contracts import ModelRepository,Model
from syft.he.paillier.keys import KeyPair
from syft.nn.linear import LinearClassifier
from sklearn.datasets import load_diabetes


app = Flask(__name__)

warnings.filterwarnings('ignore')
diabetes = load_diabetes()
y = diabetes.target
X = diabetes.data
validation = (X[0:5],y[0:5])
anonymous_diabetes_users = (X[6:],y[6:])
repo = ModelRepository('0x345ca3e014aaf5dca488057592ee47305d9b3e10', web3_host='localhost')

def get_balance(account):
    return repo.web3.fromWei(repo.web3.eth.getBalance(account),'ether')



@app.route('/')
def say_hi():
    patient_addresses = repo.web3.eth.accounts[1:10]
    anonymous_diabetics = list(zip(patient_addresses,
                               anonymous_diabetes_users[0],
                               anonymous_diabetes_users[1]))
    cure_diabetes_inc = repo.web3.eth.accounts[1]
    pubkey,prikey = KeyPair().generate(n_length=1024)
    diabetes_classifier = LinearClassifier(desc="DiabetesClassifier",n_inputs=10,n_labels=1)
    initial_error = diabetes_classifier.evaluate(validation[0],validation[1])
    diabetes_classifier.encrypt(pubkey)

    diabetes_model = Model(owner=cure_diabetes_inc,
                        syft_obj = diabetes_classifier,
                        bounty = 1,
                        initial_error = initial_error,
                        target_error = 10000
                        )
    model_id = repo.submit_model(diabetes_model)
    model = repo[model_id]
    diabetic_address,input_data,target_data = anonymous_diabetics[0]
    repo[model_id].submit_gradient(diabetic_address,input_data,target_data)
    print(repo[model_id])
    old_balance = get_balance(diabetic_address)
    print(old_balance)
    new_error = repo[model_id].evaluate_gradient(cure_diabetes_inc,repo[model_id][0],prikey,pubkey,validation[0],validation[1])
    print(new_error)
    new_balance = get_balance(diabetic_address)
    incentive = new_balance - old_balance
    print(incentive)
    return jsonify({'initial_error':initial_error,'old_balance':old_balance, 
                'new_balance': new_balance,
                'new_error':new_error, 'incentive':incentive})


app.debug = True
app.run(port=5555, host='0.0.0.0')