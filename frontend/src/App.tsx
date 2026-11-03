import { AppShell, Text, Burger, Group } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'

import SearchPage from './search_page.tsx'
import { SyllabusViewer } from './syllabus_viewer.tsx'
import { Route, Routes } from 'react-router-dom'



function App() {
  const [opened, { toggle }] = useDisclosure()

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 200, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header p="xs">
        <Group>
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Text>SyllySearch</Text>
        </Group>
        
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        <Text>Application navbar</Text>
      </AppShell.Navbar>

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
