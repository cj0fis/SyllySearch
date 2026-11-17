import { AppShell, Text } from '@mantine/core'

import SearchPage from './search_page.tsx'
import { SyllabusViewer } from './syllabus_viewer.tsx'
import { Route, Routes } from 'react-router-dom'
// import { Link } from 'react-router-dom'


function App() {
  return (
    <AppShell
      header={{ height: 80 }}
      padding="md"
    >
      <AppShell.Header
        px="xl"
        py="md"
        style={{
          backgroundColor: '#500000',
          borderBottom: 'none',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <a href="/" style={{ textDecoration: 'none' }}>
          <Text
            size="2rem"
            fw={800}
            c="white"
            lh={1.2}
          >
            SyllySearch
          </Text>
        </a>
        
      </AppShell.Header>

      <AppShell.Main>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/syllabus/:code" element={<SyllabusViewer/>} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  )
}

export default App
