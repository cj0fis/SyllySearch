import { AppShell, Text, Burger, Group } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'

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
        <Text>Application main</Text>
      </AppShell.Main>
    </AppShell>
  )
}

export default App
