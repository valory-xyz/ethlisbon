import { ChakraProvider, ColorModeScript } from '@chakra-ui/react'
import * as React from 'react'
import ReactDOM from 'react-dom'
import { MoralisProvider } from 'react-moralis'
import { App } from './App'
import theme from './theme'

ReactDOM.render(
  <React.StrictMode>
    <ColorModeScript />
    <MoralisProvider
      appId="pQpnFFzt0fnqm7ohjjGrilnxDuyGk0oLwnxmVcAH"
      serverUrl="https://1fv4kixt2gna.usemoralis.com:2053/server"
    >
        <ChakraProvider theme={theme}>
          <App />
        </ChakraProvider>
    </MoralisProvider>
  </React.StrictMode>,
  document.getElementById('root')
)
