import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({
  content,
  className = "",
}: MarkdownContentProps) {
  return (
    <div
      className={`prose prose-gray max-w-none dark:prose-invert ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Customize heading styles
          h1: ({ node, ...props }) => (
            <h1
              className="text-2xl font-bold mb-4 text-foreground"
              {...props}
            />
          ),
          h2: ({ node, ...props }) => (
            <h2
              className="text-xl font-semibold mb-3 text-foreground"
              {...props}
            />
          ),
          h3: ({ node, ...props }) => (
            <h3
              className="text-lg font-medium mb-2 text-foreground"
              {...props}
            />
          ),
          // Customize paragraph styles
          p: ({ node, ...props }) => (
            <p
              className="mb-4 text-muted-foreground leading-relaxed"
              {...props}
            />
          ),
          // Customize list styles
          ul: ({ node, ...props }) => (
            <ul
              className="mb-4 ml-6 list-disc text-muted-foreground"
              {...props}
            />
          ),
          ol: ({ node, ...props }) => (
            <ol
              className="mb-4 ml-6 list-decimal text-muted-foreground"
              {...props}
            />
          ),
          li: ({ node, ...props }) => <li className="mb-1" {...props} />,
          // Customize code styles
          code: ({ node, inline, ...props }) =>
            inline ? (
              <code
                className="px-1.5 py-0.5 rounded bg-muted text-foreground font-mono text-sm"
                {...props}
              />
            ) : (
              <code
                className="block p-4 rounded bg-muted text-foreground font-mono text-sm"
                {...props}
              />
            ),
          // Customize blockquote styles
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-primary pl-4 italic text-muted-foreground mb-4"
              {...props}
            />
          ),
          // Customize link styles
          a: ({ node, ...props }) => (
            <a
              className="text-primary hover:text-primary/80 underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
          // Customize table styles
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto mb-4">
              <table
                className="w-full border-collapse border border-border"
                {...props}
              />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-muted" {...props} />
          ),
          tbody: ({ node, ...props }) => <tbody {...props} />,
          tr: ({ node, ...props }) => (
            <tr
              className="border-b border-border hover:bg-muted/50"
              {...props}
            />
          ),
          th: ({ node, ...props }) => (
            <th
              className="border border-border px-4 py-2 text-left font-semibold text-foreground"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="border border-border px-4 py-2 text-muted-foreground"
              {...props}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
