// 1. Import `extendTheme`
import { extendTheme } from '@chakra-ui/react'

// 2. Call `extendTheme` and pass your custom values
const theme = extendTheme({
  fonts: {
    heading: 'GT Haptik',
    stat: 'Gt Haptik'
  },
})

export default theme
