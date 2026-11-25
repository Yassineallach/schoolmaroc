// Small, safe Markdown renderer: escapes all HTML first, then applies
// a limited set of formatting rules. No external dependencies.

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inline(s) {
  return s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

export function renderMarkdown(src) {
  const parts = src.split(/```/);
  let html = "";
  parts.forEach((part, i) => {
    if (i % 2 === 1) {
      const nl = part.indexOf("\n");
      const code = nl === -1 ? part : part.slice(nl + 1);
      html += `<pre><button class="copy-code" type="button">Copy</button><code>${escapeHtml(
        code.replace(/\n$/, "")
      )}</code></pre>`;
      return;
    }
    const lines = escapeHtml(part).split("\n");
    let listType = null;
    let para = [];
    const flushPara = () => {
      if (para.length) html += `<p>${inline(para.join("<br>"))}</p>`;
      para = [];
    };
    const closeList = () => {
      if (listType) html += `</${listType}>`;
      listType = null;
    };
    for (const line of lines) {
      let m;
      if ((m = line.match(/^(#{1,4})\s+(.*)/))) {
        flushPara();
        closeList();
        const level = Math.min(m[1].length + 2, 6);
        html += `<h${level}>${inline(m[2])}</h${level}>`;
      } else if ((m = line.match(/^\s*[-*]\s+(.*)/))) {
        flushPara();
        if (listType !== "ul") {
          closeList();
          html += "<ul>";
          listType = "ul";
        }
        html += `<li>${inline(m[1])}</li>`;
      } else if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) {
        flushPara();
        if (listType !== "ol") {
          closeList();
          html += "<ol>";
          listType = "ol";
        }
        html += `<li>${inline(m[1])}</li>`;
      } else if (line.trim() === "") {
        flushPara();
        closeList();
      } else {
        closeList();
        para.push(line);
      }
    }
    flushPara();
    closeList();
  });
  return html;
}
