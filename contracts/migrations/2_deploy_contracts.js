var ModelRepository = artifacts.require('./ModelRepository.sol')

module.exports = function (deployer) {
  deployer.deploy(ModelRepository,{ gas: 3000000 })
}
