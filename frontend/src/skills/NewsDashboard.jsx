import { useEffect, useMemo, useState } from "react";
import { fetchNews } from "../api";

const TOPICS = [
  { id: "ai", label: "AI" },
  { id: "tech", label: "Tech" },
  { id: "top", label: "Top" },
];

const SOURCE_NAMES = {
  "hnrss.org": "Hacker News",
  "news.ycombinator.com": "Hacker News",
  "theverge.com": "The Verge",
};

const SAVED_KEY = "sanya-news-saved";

function pad(value) {
  return String(value).padStart(2, "0");
}

function isoFromDate(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function todayISO() {
  return isoFromDate(new Date());
}

function yesterdayISO() {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  return isoFromDate(date);
}

function prettySource(source) {
  if (!source) return "News";
  const host = source.replace(/^www\./, "");
  return SOURCE_NAMES[host] || host.replace(/\.com$/, "").replace(/\./g, " ");
}

function formatPublished(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function stripHtml(value) {
  const text = (value || "").replace(/<[^>]+>/g, "").trim();
  if (!text || /^points:\s*\d+/i.test(text)) return "";
  return text;
}

function loadSaved() {
  try {
    return JSON.parse(localStorage.getItem(SAVED_KEY) || "[]");
  } catch {
    return [];
  }
}

function storyKey(item) {
  return item.url || item.title;
}

export default function NewsDashboard({ onError }) {
  const [topic, setTopic] = useState("ai");
  const [day, setDay] = useState(todayISO());
  const [payload, setPayload] = useState(null);
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [saved, setSaved] = useState(loadSaved);
  const [copied, setCopied] = useState("");

  async function load(nextTopic = topic, nextDay = day, refresh = false) {
    if (nextTopic === "saved") return;
    setBusy(true);
    onError("");
    try {
      const news = await fetchNews(nextTopic, nextDay, refresh);
      setPayload(news);
    } catch (error) {
      onError(error.message || "Could not load news.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (topic === "saved") return;
    load(topic, day);
  }, [topic, day]);

  function persistSaved(next) {
    setSaved(next);
    localStorage.setItem(SAVED_KEY, JSON.stringify(next));
  }

  function toggleSave(item) {
    const exists = saved.some((entry) => storyKey(entry) === storyKey(item));
    persistSaved(
      exists
        ? saved.filter((entry) => storyKey(entry) !== storyKey(item))
        : [{ ...item, topic, savedAt: new Date().toISOString() }, ...saved].slice(0, 40),
    );
  }

  async function copyLink(item) {
    if (!item.url) return;
    try {
      await navigator.clipboard.writeText(item.url);
    } catch {
      const field = document.createElement("textarea");
      field.value = item.url;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.left = "-9999px";
      document.body.appendChild(field);
      field.select();
      document.execCommand("copy");
      field.remove();
    }
    setCopied(storyKey(item));
    setTimeout(() => setCopied(""), 1400);
  }

  const stories = topic === "saved" ? saved : payload?.items || [];
  const sources = [...new Set(stories.map((item) => prettySource(item.source)))].filter(Boolean);
  const visible = useMemo(() => {
    return stories.filter((item) => {
      const haystack = `${item.title} ${item.summary} ${item.source}`.toLowerCase();
      if (search && !haystack.includes(search.toLowerCase())) return false;
      if (source && prettySource(item.source) !== source) return false;
      return true;
    });
  }, [stories, search, source]);

  const featured = visible[0];
  const rest = visible.slice(1);
  const today = todayISO();
  const yesterday = yesterdayISO();

  return (
    <div className="news-page">
      <header className="page-head">
        <div>
          <h2>News</h2>
        </div>
      </header>

      <section className="todo-toolbar">
        <input
          className="todo-search"
          placeholder="Search headlines..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="news-when">
          <div className="news-when-days">
            <button
              className={day === today ? "active" : ""}
              type="button"
              disabled={topic === "saved"}
              onClick={() => {
                setTopic((current) => (current === "saved" ? "ai" : current));
                setDay(today);
              }}
            >
              Today
            </button>
            <button
              className={day === yesterday ? "active" : ""}
              type="button"
              disabled={topic === "saved"}
              onClick={() => {
                setTopic((current) => (current === "saved" ? "ai" : current));
                setDay(yesterday);
              }}
            >
              Yesterday
            </button>
          </div>
          <div className="news-when-tools">
            <input
              type="date"
              aria-label="Select date"
              value={day}
              max={today}
              onChange={(event) => {
                if (!event.target.value) return;
                setTopic((current) => (current === "saved" ? "ai" : current));
                setDay(event.target.value);
              }}
              disabled={topic === "saved"}
            />
            <button
              className="todo-add-btn"
              type="button"
              disabled={busy || topic === "saved"}
              onClick={() => {
                setTopic((current) => (current === "saved" ? "ai" : current));
                setDay(today);
                load(topic === "saved" ? "ai" : topic, today, true);
              }}
            >
              {busy ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>
        <nav className="news-topics">
          {TOPICS.map((item) => (
            <button
              key={item.id}
              className={topic === item.id ? "active" : ""}
              type="button"
              onClick={() => {
                setSearch("");
                setSource("");
                setTopic(item.id);
              }}
            >
              {item.label}
              {topic === item.id ? <span>{payload?.items?.length || 0}</span> : null}
            </button>
          ))}
          <button
            className={`news-saved ${topic === "saved" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setSearch("");
              setSource("");
              setTopic("saved");
            }}
          >
            Saved
            <span>{saved.length}</span>
          </button>
        </nav>
        {sources.length > 1 ? (
          <div className="news-sources">
            <button className={!source ? "active" : ""} type="button" onClick={() => setSource("")}>
              All sources
            </button>
            {sources.map((name) => (
              <button
                key={name}
                className={source === name ? "active" : ""}
                type="button"
                onClick={() => setSource(name === source ? "" : name)}
              >
                {name}
              </button>
            ))}
          </div>
        ) : null}
      </section>

      {!visible.length ? (
        <div className="todo-empty">
          <strong>{busy ? "Fetching headlines…" : "No stories here"}</strong>
          <p>{busy ? "Give it a moment." : "No headlines were saved for this day."}</p>
        </div>
      ) : null}

      {featured ? (
        <StoryCard
          item={featured}
          featured
          saved={saved.some((entry) => storyKey(entry) === storyKey(featured))}
          copied={copied === storyKey(featured)}
          onSave={() => toggleSave(featured)}
          onCopy={() => copyLink(featured)}
        />
      ) : null}

      <section className="news-grid">
        {rest.map((item) => (
          <StoryCard
            key={storyKey(item)}
            item={item}
            saved={saved.some((entry) => storyKey(entry) === storyKey(item))}
            copied={copied === storyKey(item)}
            onSave={() => toggleSave(item)}
            onCopy={() => copyLink(item)}
          />
        ))}
      </section>
    </div>
  );
}

function StoryCard({ item, featured = false, saved, copied, onSave, onCopy }) {
  const summary = stripHtml(item.summary);
  const time = formatPublished(item.published);
  function openStory() {
    if (!item.url) return;
    window.open(item.url, "_blank", "noopener,noreferrer");
  }
  return (
    <article
      className={`news-story ${featured ? "featured" : ""} ${item.url ? "openable" : ""}`}
      onClick={openStory}
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget) return;
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openStory();
        }
      }}
      role={item.url ? "link" : undefined}
      tabIndex={item.url ? 0 : undefined}
    >
      <div className="news-story-top">
        <div className="news-story-meta">
          <span className="chip">{prettySource(item.source)}</span>
          {time ? <span className="news-time">{time}</span> : null}
        </div>
        <div className="news-story-actions" onClick={(event) => event.stopPropagation()}>
          <button type="button" aria-label={copied ? "Copied" : "Copy link"} title={copied ? "Copied" : "Copy"} onClick={onCopy}>
            {copied ? <CheckIcon /> : <CopyIcon />}
          </button>
          <button
            className={saved ? "saved" : ""}
            type="button"
            aria-label={saved ? "Saved" : "Save"}
            title={saved ? "Saved" : "Save"}
            onClick={onSave}
          >
            <SaveIcon filled={saved} />
          </button>
        </div>
      </div>
      <h3>{item.title}</h3>
      {summary ? <p>{summary}</p> : null}
    </article>
  );
}

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M6 16H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12.5 9.2 17 19 7" />
    </svg>
  );
}

function SaveIcon({ filled }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={filled ? "filled" : ""}>
      <path d="M7 4.5h10a1 1 0 0 1 1 1V20l-6-3.2L6 20V5.5a1 1 0 0 1 1-1z" />
    </svg>
  );
}
