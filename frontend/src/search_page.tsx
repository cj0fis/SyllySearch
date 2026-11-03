// import {react} from 'react'
import { useState, useEffect } from 'react'
import { Badge, Button, Card, Divider, Group, Input, Stack, Text, Tooltip } from '@mantine/core'

import type { QueryResponse, SearchResult } from './types'
import { Link } from 'react-router-dom'

function ScorePill({ label, value, color }: { label: string, value: string | number | null, color: string }) {
  if (value === null) return null
  return (
    <Tooltip label={label}>
      <Badge color={color} variant='light' size='lg'>
        {label}: {value}
      </Badge>
    </Tooltip>
  )
}

function ResultCard({ result }: { result: SearchResult }) {
  const { doc, rating, difficulty, gpa, score } = result;

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Stack gap="xs">
        <Group justify="space-between" align="flex-start">
          <Stack gap={2}>
            <Text fw={700} size="lg">
              {doc.course_code} — {doc.subtitle}
            </Text>

            <Text size="sm" c="dimmed">
              {doc.term} · Section {doc.section}
            </Text>
          </Stack>

          <Badge color="blue" variant="filled" size="lg">
            Score: {(score * 100).toFixed(1)}%
          </Badge>
        </Group>

        <Group gap="xs">
          <Text size="sm" c="dimmed">
            {doc.instructors
              .map((instructor) => `${instructor.first} ${instructor.last}`)
              .join(", ")}
          </Text>

          <ScorePill
            label="Prof. Rating"
            value={`${(rating * 100).toFixed(1)}%`}
            color="green"
          />

          <ScorePill
            label="Prof. Difficulty"
            value={`${(difficulty * 100).toFixed(1)}%`}
            color="orange"
          />
        </Group>

        <Divider />

        <Text size="sm" lineClamp={3}>
          {doc.description}
        </Text>

        <Group justify="space-between" align="center">
          <Group gap="xs">
            <ScorePill
              label="GPA"
              value={(gpa*4).toFixed(2)}
              color="teal"
            />

            {doc.has_text && (
              <Badge color="violet" variant="light">
                Has Syllabus
              </Badge>
            )}
          </Group>

          {doc.code && (
            <Button
              component={Link}
              to={`/syllabus/${encodeURIComponent(doc.code)}`}
              variant="light"
              color="blue"
            >
              View syllabus
            </Button>
          )}
        </Group>
      </Stack>
    </Card>
  );
}

export default function SearchPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<SearchResult[] | null>(null)




    useEffect(() => {
        if (query.trim() === '')
            return

        const delay = setTimeout(async () => {
            try {
                const response = await fetch(`http://localhost:8080/query?query_text=${encodeURIComponent(query)}`)
                const data: QueryResponse = await response.json()
                setResults(data[1])
            } catch (error) {
                console.error('Search failed:', error)
            }
        }, 500)

        return () => clearTimeout(delay)
    }, [query])
    return (
    <Stack>
      <Text size='xl'>Search</Text>
      <Input
        placeholder="Search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      
      {results && results.map((result, index) => (
        <ResultCard key={index} result={result} />
      ))}
    </Stack>
  )
}