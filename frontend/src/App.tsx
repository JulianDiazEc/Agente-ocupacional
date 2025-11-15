import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { theme } from '@/theme'
// import AppRoutes from './routes'
// import { ProcessingProvider } from '@/contexts/ProcessingContext'

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        {/* <ProcessingProvider> */}
          <div>
            <h1>Narah HC Processor</h1>
            <p>Sistema de procesamiento de historias clínicas ocupacionales</p>
            {/* <AppRoutes /> */}
          </div>
        {/* </ProcessingProvider> */}
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
