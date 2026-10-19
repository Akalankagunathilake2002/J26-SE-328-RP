import React from "react";

/** Renders the small markdown subset Skillaro writes (paragraphs, ### headings, - / 1. lists, ``` code
 *  blocks, **bold**, `code`) as React elements. No HTML is injected, so model output can't run script. */
export default function SimpleMarkdown({ text, className = "" }: { text: string; className?: string }) {
  const blocks: React.ReactNode[] = [];
  const lines = text.replace(/\r/g, "").split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim().startsWith("```")) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) code.push(lines[i++]);
      i++;
      blocks.push(
        <pre key={blocks.length} className="overflow-x-auto border border-ink bg-ink/90 p-3 font-mono text-[12px] leading-relaxed text-cream">
          <code>{code.join("\n")}</code>
        </pre>
      );
    } else if (/^\s*([-*•]|\d+[.)])\s+/.test(line)) {
      const ordered = /^\s*\d/.test(line);
      const items: string[] = [];
      while (i < lines.length && /^\s*([-*•]|\d+[.)])\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*•]|\d+[.)])\s+/, ""));
        i++;
      }
      const List = ordered ? "ol" : "ul";
      blocks.push(
        <List key={blocks.length} className={`space-y-1 pl-5 ${ordered ? "list-decimal" : "list-disc"}`}>
          {items.map((item, j) => (
            <li key={j}>{inline(item)}</li>
          ))}
        </List>
      );
    } else if (/^#{1,4}\s/.test(line)) {
      blocks.push(
        <p key={blocks.length} className="font-bold text-ink">
          {inline(line.replace(/^#{1,4}\s/, ""))}
        </p>
      );
      i++;
    } else if (line.trim()) {
      const para: string[] = [];
      while (i < lines.length && lines[i].trim() && !/^\s*([-*•]|\d+[.)])\s+|^#{1,4}\s|^\s*```/.test(lines[i])) {
        para.push(lines[i++]);
      }
      blocks.push(<p key={blocks.length}>{inline(para.join(" "))}</p>);
    } else {
      i++;
    }
  }
  return <div className={`space-y-2 ${className}`}>{blocks}</div>;
}

function inline(text: string): React.ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`"))
      return (
        <code key={i} className="border border-ink/30 bg-sand px-1 font-mono text-[0.9em]">
          {part.slice(1, -1)}
        </code>
      );
    return part;
  });
}
