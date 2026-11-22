import React from "react";

/** Renders the markdown Skillaro writes as React elements (no HTML is injected, so model output can't run
 *  script): paragraphs, # headings, - / 1. lists, > quotes, ``` code blocks, **bold**, *emphasis*, `code`
 *  and [links](https://…). Emphasis is highlighted rather than italic: these pages set text upright. */
export default function SimpleMarkdown({ text, className = "" }: { text: string; className?: string }) {
  const blocks: React.ReactNode[] = [];
  const lines = text.replace(/\r/g, "").split("\n");
  const LIST = /^\s*([-*•]|\d+[.)])\s+/;
  const HEADING = /^#{1,4}\s/;
  const QUOTE = /^\s*>\s?/;
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim().startsWith("```")) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) code.push(lines[i++]);
      i++;
      blocks.push(
        <pre key={blocks.length} className="overflow-x-auto border-2 border-ink bg-ink p-3 font-mono text-[12.5px] leading-relaxed text-cream">
          <code>{code.join("\n")}</code>
        </pre>
      );
    } else if (LIST.test(line)) {
      const ordered = /^\s*\d/.test(line);
      const items: string[] = [];
      while (i < lines.length && LIST.test(lines[i])) items.push(lines[i++].replace(LIST, ""));
      const List = ordered ? "ol" : "ul";
      blocks.push(
        <List key={blocks.length} className={`space-y-1.5 pl-5 marker:font-bold marker:text-brand-blue ${ordered ? "list-decimal" : "list-disc"}`}>
          {items.map((item, j) => (
            <li key={j} className="pl-1">{inline(item)}</li>
          ))}
        </List>
      );
    } else if (HEADING.test(line)) {
      const level = line.match(/^#+/)![0].length;
      blocks.push(
        <p key={blocks.length} className={`pt-1 font-bold text-ink ${level <= 2 ? "text-base" : "text-[0.95rem]"}`}>
          {inline(line.replace(HEADING, ""))}
        </p>
      );
      i++;
    } else if (QUOTE.test(line)) {
      const quote: string[] = [];
      while (i < lines.length && QUOTE.test(lines[i])) quote.push(lines[i++].replace(QUOTE, ""));
      blocks.push(
        <blockquote key={blocks.length} className="border-l-4 border-brand-blue bg-cream px-3 py-2 text-ink">
          {inline(quote.join(" "))}
        </blockquote>
      );
    } else if (line.trim()) {
      const para: string[] = [];
      while (i < lines.length && lines[i].trim() && !LIST.test(lines[i]) && !HEADING.test(lines[i]) &&
             !QUOTE.test(lines[i]) && !lines[i].trim().startsWith("```")) {
        para.push(lines[i++]);
      }
      blocks.push(<p key={blocks.length}>{inline(para.join(" "))}</p>);
    } else {
      i++;
    }
  }
  return <div className={`space-y-3 ${className}`}>{blocks}</div>;
}

// **bold**, `code`, [text](https://url), and *emphasis* or _emphasis_ (not inside words, so snake_case stays)
const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)\s]+\)|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*])|(?<!\w)_[^_\s][^_]*?_(?!\w))/g;
const LINK = /^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/;

function inline(text: string): React.ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i} className="font-bold">{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`"))
      return (
        <code key={i} className="border border-ink/25 bg-sand px-1 py-px font-mono text-[0.88em]">
          {part.slice(1, -1)}
        </code>
      );
    const link = part.match(LINK);
    if (link)
      return (
        <a key={i} href={link[2]} target="_blank" rel="noopener noreferrer" className="font-semibold text-brand-blue underline underline-offset-2">
          {link[1]}
        </a>
      );
    if (part.length > 2 && ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))))
      return (
        <em key={i} className="bg-butter/70 px-0.5 font-semibold not-italic text-ink">
          {part.slice(1, -1)}
        </em>
      );
    return part;
  });
}
