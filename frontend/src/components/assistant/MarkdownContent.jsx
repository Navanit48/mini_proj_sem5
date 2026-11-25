
const inline = (text) => {
  const parts = [];
  const tokenPattern = /(\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let cursor = 0;
  for (const match of text.matchAll(tokenPattern)) {
    if (match.index > cursor) parts.push(text.slice(cursor, match.index));
    const token = match[0];
    if (token.startsWith('**')) {
      parts.push(<strong key={match.index} className="font-semibold text-foreground">{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('*')) {
      parts.push(<em key={match.index}>{token.slice(1, -1)}</em>);
    } else {
      const parsed = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      const href = parsed?.[2] || '#';
      const safe = href.startsWith('/') || href.startsWith('https://') || href.startsWith('http://');
      parts.push(safe
        ? <a key={match.index} href={href} className="text-primary underline underline-offset-2" target={href.startsWith('http') ? '_blank' : undefined} rel={href.startsWith('http') ? 'noreferrer' : undefined}>{parsed[1]}</a>
        : parsed?.[1]);
    }
    cursor = match.index + token.length;
  }
  if (cursor < text.length) parts.push(text.slice(cursor));
  return parts;
};

const MarkdownContent = ({ content }) => {
  const rows = String(content || '').split('\n');
  const blocks = [];
  for (let i = 0; i < rows.length;) {
    const line = rows[i].trim();
    if (!line) { i += 1; continue; }

    if (line.includes('|') && rows[i + 1]?.includes('|') && /^\s*\|?\s*:?-{3,}/.test(rows[i + 1])) {
      const parseCells = (row) => row.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
      const headers = parseCells(line);
      i += 2;
      const body = [];
      while (i < rows.length && rows[i].includes('|')) body.push(parseCells(rows[i++]));
      blocks.push(
        <div key={'table-' + i} className="my-3 overflow-x-auto rounded-lg border border-border">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-secondary/70"><tr>{headers.map((cell, index) => <th key={index} className="px-3 py-2 font-semibold">{inline(cell)}</th>)}</tr></thead>
            <tbody>{body.map((row, r) => <tr key={r} className="border-t border-border">{headers.map((_, c) => <td key={c} className="px-3 py-2 text-muted-foreground">{inline(row[c] || '')}</td>)}</tr>)}</tbody>
          </table>
        </div>
      );
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      const Tag = 'h' + heading[1].length;
      blocks.push(<Tag key={i} className="mb-2 mt-3 font-semibold text-foreground">{inline(heading[2])}</Tag>);
      i += 1;
      continue;
    }
    if (/^[-*]\s+/.test(line) || /^\d+[.)]\s+/.test(line)) {
      const ordered = /^\d+[.)]/.test(line);
      const items = [];
      while (i < rows.length && (/^\s*[-*]\s+/.test(rows[i]) || /^\s*\d+[.)]\s+/.test(rows[i]))) {
        items.push(rows[i++].replace(/^\s*(?:[-*]|\d+[.)])\s+/, ''));
      }
      const Tag = ordered ? 'ol' : 'ul';
      blocks.push(<Tag key={'list-' + i} className={ordered ? 'my-2 list-decimal space-y-1 pl-5' : 'my-2 list-disc space-y-1 pl-5'}>{items.map((item, index) => <li key={index}>{inline(item)}</li>)}</Tag>);
      continue;
    }
    const paragraph = [line];
    i += 1;
    while (i < rows.length && rows[i].trim() && !/^(#{1,3})\s|^[-*]\s|^\d+[.)]\s/.test(rows[i].trim())) paragraph.push(rows[i++].trim());
    blocks.push(<p key={'p-' + i} className="my-2 leading-6">{inline(paragraph.join(' '))}</p>);
  }
  return <div className="text-sm text-muted-foreground">{blocks}</div>;
};

export default MarkdownContent;
