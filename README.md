## What is chAIn?
The goal of the chAIn project is to develop an AI+Blockchain-powered decentralised bank. As a starting point we want to focus on developing a truly peer-to-peer lending platform, to develop *links* between different entities *chaining* their interests together. The problem with relying purely on smart contracts is that it is necessary to evaluate the risks and rewards involved. Smart contracts on their own can take the place of trusted intermediaries but often these intermediaries, such as financial organisations and law firms also provide expert knowledge that cannot necessarily be replicated by an ordinary smart contract. Increasingly however machine learning algorithms are able to perform many expert tasks. Fintech companies such as challenger banks often rely on vast quantities of data to provide alternative kinds of products and services, for example lending money to a more diverse group of clients. However it is important that the people whose data is used to build algorithms are also compensated in some way. 

Our aim was to combine these two cutting edge technologies to decentralise financial services so that value can be intelligently directed to where it is needed with minmal intervention from third parties. We were inspired the [OpenMined](https://openmined.org) project and leverage its [open source codebase](https://github.com/OpenMined).  The key to the OpenMined project is a method called homomorphic encryption which allows machine learning algorithms to be trained locally on a user's device without revealing the details of the algorithm so that it cannot be modified by malicious actors, whilst preserving the privacy of the user's data. 

## How does it work?
The chAIn project is built upon the framework proposed by OpenMined. There are two important components, each of which can have their own set of smart contracts:

1. Model training
- People who wish to lend (the codebase has the idea of 'the company' for the sake of simplicity but they also be a group of individuals) create a smart contract via which they assign a sum of money ('the bounty') that will be distributed to people who share their data. They also decide on an machine learning model, a target accuracy that the model should be trained to meet, and a mechanism for dividing bounty among those who share their data. 
- Individuals (we refer to them as 'data owners') can share their personal financial details in return for a reward. They are incentivised to share the data, knowing that not only will they be rewarded but that privacy will be maintained. 

2. Model deployment
- Once the model has been trained i.e. when its accuracy reaches or exceeds the target, it can then be deployed via another smart contract. Predictions like risk of default can be made on potential borrower's data to make a decision as to whether or not to lend and the rate of interest to charge.

Due to time constraints we focussed on just the first part of this system i.e. model training.

The process is illustrated in the architecture diagram below.

![](https://github.com/Riksi/chAIn/blob/master/architecture.jpg)

You can watch a video [here](https://www.youtube.com/watch?v=pDOv89Rc-78).

## Why blockchain?
Here we summarise some the ideas put forward in the OpenMinded project that interested us the most (we summarise them as we understand them - if we have misstated any of these, we apologise sincerely).

1. We can store the official state of hte model across distributed clients.
2. There is potential for the system of incentives to develop into a cryptocurrency system with its own token
3. It is simpler to create and manage incentives via smart contracts and theoretically impossible to game the system
4. The process is inherently distributed, which makes it conducive to a decentralised architecture

## The tech
Our system consists of a smart contract and pair of applications, one for the use of the lender and one for the use of data-owner. 

The contract is found in ModelRepository.sol and was based on OpenMined's demo with some of our own modifications. For simplicity we implemented the applications as Flask apps to be run locally and accessed via a browser. The main functionality is found in the files company.py and data-owner.py. We relied on the simple demo presented OpenMined's IPython notebook 'Sonar - Decentralized Learning Demo.ipynb' but built it out into two different applications for the system. Through these apps the lenders can manage the contract and models whilst the data-owner can share their data. 

In order to communicate with the contract, the module web3.py is used by these applications. We also rely on OpenMined's repositories [Sonar](https://github.com/OpenMined/Sonar), [PySonar](https://github.com/OpenMined/PySonar), and, crucially, for encrypted machine learning, its repository, [PySyft](https://github.com/OpenMined/PySyft). Due to the lack of functionality for mathematical operations in the present state of the library we used a linear classifier in this first stage of the project. For out system to work, setup instructions provided by each of these repositories need to be followed in order to create a contract and install all the necessary modules.

A Python based application was needed for the lender and the data-owner because we have to do machine learning off-chain, whilst on the chain, rewards are calculated and incentives are transferred appropriately. Also the contract stores the addresses of the model data which is stored on the decentralised InterPlanetary File System since the data is too large to be stored on chain. 

For model training, to simulate data-owners sending data, we used the data provided by [Lending Club](https://www.lendingclub.com/info/download-data.action).

## Where next
Of course there is much more we can do even to develop the peer-to-peer lending system. Here are some important areas where we want to focus:

1. Build and train more sophisticated classifiers and simulate the involvement of many data-owners sending their data
2. Create a more complex smart contracts - for example dealing with attempts to resend same data whilst allowing different data to be sent at different times by same data-owner (where this is appropriate e.g. bank statements)
3. Package the applications so that users can easily download and run them
4. Deploy the model 
5. Develop a token for this system
6. Extend this framework to other financial services e.g. insurance.



