export interface Instructor {
    id: string
    first: string
    last: string
}

export interface Syllabus {
    id: string
    code: string
    dept: string
    course_number: string
    section: string
    term: string
    subtitle: string
    course_code: string
    description: string
    has_text: boolean
    instructors: Instructor[]
}

export interface SearchResult {
    doc: Syllabus
    bm25f: number
    rating: number
    difficulty: number
    gpa: number
    score: number
}

export interface ParsedQuery {
    intent: string | null
    level: string | null
    dept: string | null
    course: [string, string] | null
    text: string | null
}

export type QueryResponse = [ParsedQuery, SearchResult[]]