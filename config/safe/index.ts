import { ethers, Wallet } from 'ethers'
import Safe, { ContractNetworksConfig, EthersAdapter } from '@gnosis.pm/safe-core-sdk'
import { SafeFactory, SafeAccountConfig } from '@gnosis.pm/safe-core-sdk'

require('dotenv').config()

const provider = new ethers.providers.JsonRpcProvider(process.env.INFURA_ROPSTEN);
const signer = new Wallet(process.env.SIGNER_PKEY, provider);

const ethAdapter = new EthersAdapter({
  ethers,
  signer: signer
});

// Ropsten Gnosis contracts
const contractNetworks: ContractNetworksConfig = {
    '3':  {
        /** multiSendAddress - Address of the MultiSend contract deployed on a specific network */
        // NOTE: multiSendAddress contract not deployed on ropsten, put any contract address as placeholder except 0x address
        multiSendAddress: '0x76E2cFc1F5Fa8F6a5b3fC4c8F4788F0116861F9B',
        /** safeMasterCopyAddress - Address of the Gnosis Safe Master Copy contract deployed on a specific network */
        safeMasterCopyAddress: '0x6851D6fDFAfD08c0295C392436245E5bc78B0185',
        /** safeProxyFactoryAddress - Address of the Gnosis Safe Proxy Factory contract deployed on a specific network */
        safeProxyFactoryAddress: '0x76E2cFc1F5Fa8F6a5b3fC4c8F4788F0116861F9B'
    }
};

(async function deploySafe(){
    const safeFactory = await SafeFactory.create({ ethAdapter, contractNetworks })
    // add owners here
    const owners = []
    // add quorum here
    const threshold = 0
    const safeAccountConfig: SafeAccountConfig = { owners, threshold }
    const safeSdk: Safe = await safeFactory.deploySafe(safeAccountConfig)    
    const newSafeAddress = safeSdk.getAddress()
    console.log(`New safe address is ${newSafeAddress}`)
})()


