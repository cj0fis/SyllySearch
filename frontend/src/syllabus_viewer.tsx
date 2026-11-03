import { useEffect, useState } from "react";
import DOMPurify from "dompurify";
import "./syllabus_viewer.css"
import { Link, useParams } from "react-router-dom";

type SyllabusComponent = {
  component_id: string;
  html: string;
  sort_order: number;
  is_public: boolean;
};

type Syllabus = {
  title: string;
  sub_title: string;
  term: {
    name: string;
  };
  components: SyllabusComponent[];
};

type ApiResponse = {
  sys: {
    success: boolean;
  };
  items: Array<{
    doc_data: Syllabus;
  }>;
};

type Props = {
  code: string;
};

const SIMPLE_SYLLABUS_URL = "https://tamu.simplesyllabus.com";

function sanitizeHtml(html: string) {
  // Make relative links and images point to the original website.
  const absoluteHtml = html
    .replaceAll('src="/', `src="${SIMPLE_SYLLABUS_URL}/`)
    .replaceAll('href="/', `href="${SIMPLE_SYLLABUS_URL}/`);

  return DOMPurify.sanitize(absoluteHtml);
}

export function SyllabusViewer() {
  const { code } = useParams<{ code: string }>();
  if (!code) {
    return (
      <main>
        <p>No syllabus code was provided.</p>
        <Link to="/">Go back to the search page</Link>
      </main>
    )
  }
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    async function loadSyllabus() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `/api/syllabus?code=${encodeURIComponent(code!)}`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }

        const data = (await response.json()) as ApiResponse;
        const document = data.items[0]?.doc_data;

        if (!data.sys.success || !document) {
          throw new Error("Syllabus not found.");
        }

        setSyllabus(document);
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(
            error instanceof Error
              ? error.message
              : "Unable to load syllabus.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadSyllabus();

    return () => controller.abort();
  }, [code]);

  if (loading) {
    return <p>Loading syllabus…</p>;
  }

  if (error) {
    return <p role="alert">{error}</p>;
  }

  if (!syllabus) {
    return null;
  }

  const components = syllabus.components
    .filter((component) => component.is_public)
    .sort((a, b) => a.sort_order - b.sort_order);

  return (
    <article className="syllabus">
      <header className="syllabus-header">
        <p>{syllabus.term.name}</p>
        <h1>{syllabus.title}</h1>
        <p>{syllabus.sub_title}</p>
      </header>

      {components.map((component) => (
        <section
          key={component.component_id}
          className="syllabus-section"
          dangerouslySetInnerHTML={{
            __html: sanitizeHtml(component.html),
          }}
        />
      ))}
    </article>
  );
}