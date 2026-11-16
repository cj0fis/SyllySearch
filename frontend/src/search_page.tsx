// import {react} from 'react'
import { useState, useEffect } from 'react'
import { Badge, Card, Divider, Group, Input, Stack, Text, Progress } from '@mantine/core'

import type { QueryResponse, SearchResult } from './types'
import { useNavigate, useSearchParams } from 'react-router-dom'

// replaced the ScorePills with visual bars to display the info
// thought it would be more interesting to look at
// also visually quicker to compare between cards than looking at direct value of ScorePill
function ScoreBar({label, value, displayValue, color}: {label: string; value: number; displayValue: string; color: string;}) {
  return (
    <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
      <Text size="xs" c="dimmed">
        {label}
      </Text>

      <Text size="sm" fw={700}>
        {displayValue}
      </Text>

      <Progress
        value={Math.max(0, Math.min(100, value))}
        color={color}
        size="sm"
        radius="xl"
      />
    </Stack>
  );
}

function ResultCard({ result }: { result: SearchResult }) {
  const { doc, rating, difficulty, gpa, score } = result;
  const navigate = useNavigate();
  const syllabusPath = doc.code
    ? `/syllabus/${encodeURIComponent(doc.code)}`
    : null;

  return (
    <Card
      shadow="sm"
      padding="lg"
      radius="md"
      withBorder
      className={syllabusPath ? 'course-card' : undefined}
      onClick={() => {
        if (syllabusPath) navigate(syllabusPath);
      }}
      style={{
        cursor: syllabusPath ? 'pointer' : 'default',
      }}
    >
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

        <Text size="sm" c="dimmed">
          {doc.instructors
            .map((instructor) => `${instructor.first} ${instructor.last}`)
            .join(", ")}
        </Text>

        <Divider />

        <Text size="sm" lineClamp={3}>
          {doc.description}
        </Text>

        <Group gap="md" grow align="flex-start">
          <ScoreBar
            label="Prof. Rating"
            value={rating * 100}
            displayValue={`${(rating * 100).toFixed(1)}%`}
            color="green"
          />

          <ScoreBar
            label="Prof. Difficulty"
            value={difficulty * 100}
            displayValue={`${(difficulty * 100).toFixed(1)}%`}
            color="orange"
          />

          <ScoreBar
            label="Course Avg. GPA"
            value={gpa * 100}
            displayValue={(gpa * 4).toFixed(2)}
            color="#A63737"
          />
        </Group>

        <Group justify="space-between" align="center">
          <Group gap="xs">
            {doc.has_text && (
              <Badge color="violet" variant="light">
                Has Syllabus
              </Badge>
            )}
          </Group>
        </Group>
      </Stack>
    </Card>
  );
}

export default function SearchPage() {
    // ADDED: Read and update the query in the URL
    // added to allow for read/updating the query stored in the URL
    // will allow user to navigate back to existing results after viewing syllabus
    const [searchParams, setSearchParams] = useSearchParams();
    const [query, setQuery] = useState(
      () => searchParams.get('q') ?? ''
    );
    const [results, setResults] = useState<SearchResult[] | null>(null)




    useEffect(() => {
        if (query.trim() === '') {
            setResults(null);
            return;
        }

        const delay = setTimeout(async () => {
            try {
                const ENDPOINT = import.meta.env.DEV
                  ? "http://localhost:8000"         // in dev mode, connect to localhost backend
                  : "https://api.caseyroper.com"    // in build mode, connect to deployed backend

                const response = await fetch(`${ENDPOINT}/query?query_text=${encodeURIComponent(query)}`)
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
        placeholder= 'Try "CSCE 221", "data structures", or "hard CSCE course"'
        value={query}
        onChange={(e) => {
          const newQuery = e.target.value;

          setQuery(newQuery);

          // save query in URL so user can navigate back to their existing results page instead of wiping their progress
          setSearchParams(
            newQuery ? { q: newQuery } : {},
            { replace: true }
          );
        }}
      /> 
      {results && results.map((result, index) => (
        <ResultCard key={index} result={result} />
      ))}
    </Stack>
  )
}