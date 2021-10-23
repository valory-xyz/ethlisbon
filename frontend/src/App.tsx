import {
  Box,
  Button,
  Flex,
  Grid,
  GridItem,
  Heading,
  Img,
  Input,
  Stat,
  StatLabel,
  StatNumber,
  Text,
} from '@chakra-ui/react'
import Moralis from 'moralis'
import * as React from 'react'
import {
  useMoralis,
  useMoralisWeb3Api,
  useMoralisWeb3ApiCall,
  useWeb3Transfer,
} from 'react-moralis'
import { ColorModeSwitcher } from './ColorModeSwitcher'
import Wallet from './components/Wallet'

export const App = () => {
  const [donateAmt, setDonateAmt] = React.useState(0)

  const { isAuthenticated } = useMoralis()
  const Web3Api = useMoralisWeb3Api()

  const { data, error, isLoading } = useMoralisWeb3ApiCall(
    Web3Api.account.getNativeBalance,
    {
      address: '0x2cab92c1e9d2a701ca0411b0ff35a0907ca31f7f',
      chain: 'ropsten',
    }
  )

  const {
    data: dataNFTs,
    error: errorNFTs,
    isLoading: isLoadingNFTs,
  } = useMoralisWeb3ApiCall(Web3Api.account.getNFTs, {
    address: '0x2cab92c1e9d2a701ca0411b0ff35a0907ca31f7f',
    chain: 'ropsten',
  })

  const {
    fetch,
    error: submitError,
    isFetching: isSubmitting,
  } = useWeb3Transfer({
    amount: Moralis.Units.ETH(donateAmt),
    receiver: '0x2cab92c1e9d2a701ca0411b0ff35a0907ca31f7f',
    type: 'native',
  })

  const handleSubmit = (e: any) => {
    e.preventDefault()
    console.log(donateAmt)
    fetch()
    if (isSubmitting) {
      console.log('isSubmitting')
    }
  }

  return (
    <Box vh="100">
      <Flex
        p={6}
        alignItems="center"
        justifyContent="space-between"
        borderBottomWidth={1}
      >
        <Heading size="md">Collectooorr Mek</Heading>
        <Flex>
          <Wallet />
          <ColorModeSwitcher />
        </Flex>
      </Flex>
      <Box p={6}>
        <Grid templateColumns={[1, "repeat(12, 1fr)"]} gap={6}>
          <GridItem colSpan={9}>
            <Heading mb={3}>Collection</Heading>
            <Flex mb={5}>
              <Stat>
                <Box>
                  <StatLabel>Pieces Collected</StatLabel>
                  <StatNumber fontSize="4xl">{dataNFTs?.total}</StatNumber>
                </Box>
              </Stat>
            </Flex>
            <Box>
              <Grid templateColumns="repeat(3, 1fr)" gap={6}>
                {isLoadingNFTs
                  ? 'Loading NFTs...'
                  : !error
                  ? dataNFTs?.result
                      ?.filter((nft) => nft.name === 'Art Blocks')
                      .filter((nft, i) => i < 1)
                      .map((nft) => {
                        const metadata = JSON.parse(nft?.metadata || '{}')

                        return (
                          <Box key={nft.token_id}>
                            <Heading size="sm">{metadata.name}</Heading>
                            <Text mb={2}>Last sale price: 5ETH</Text>
                            {/* <Text mb={2}>{JSON.stringify(metadata)}</Text> */}
                            <Img
                              src={`https://api.artblocks.io/image/${metadata.tokenID}`}
                            />
                          </Box>
                        )
                      })
                  : 'Error loading NFTs'}
              </Grid>
            </Box>
          </GridItem>
          <GridItem colSpan={3}>
            <Heading mb={3}>Fund</Heading>
            <Stat>
              <Box mb={3}>
                <StatLabel>Total Deposits</StatLabel>
                <StatNumber fontSize="4xl">{data ?  Number(Moralis.Units.FromWei(data?.balance, 18)) : '--'} ETH</StatNumber>
              </Box>
            </Stat>
            <form onSubmit={(e) => handleSubmit(e)}>
              <Input
                disabled={!isAuthenticated}
                onChange={(e) => setDonateAmt(Number(e.target.value))}
                mb={2}
              />
              <Button mb={2} disabled={!isAuthenticated} type="submit">
                Donate
              </Button>
              {!isAuthenticated && (
                <Text mb={2}>Connect MetaMask to donate</Text>
              )}
              {submitError && submitError.message}
            </form>
          </GridItem>
        </Grid>
      </Box>
    </Box>
  )
}
