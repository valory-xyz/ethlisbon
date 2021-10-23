import { Box, Button, Text } from '@chakra-ui/react'
import React from 'react'
import { useMoralis } from 'react-moralis'
// import { useWallet } from 'use-wallet'

function Wallet() {
  // const wallet = useWallet()
  const { authenticate, isAuthenticated, logout } = useMoralis()

  return (
    <>
      <Box>
        {isAuthenticated ? (
          <Button onClick={() => logout()}>Disconnect</Button>
        ) : (
          <Button onClick={() => authenticate()}>Connect MetaMask</Button>
        )}
      </Box>
    </>
  )
}

export default Wallet

// {wallet.status === 'connected' ? (
//   <Box textAlign="right">
//     {/* <Text>Account: {wallet.account}</Text>
//     <Text>Balance: {wallet.balance} ETH</Text> */}
//     <Button onClick={() => wallet.reset()}>Disconnect</Button>
//   </Box>
// ) : (
// )}
