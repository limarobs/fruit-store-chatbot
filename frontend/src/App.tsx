import { useEffect, useRef, useState } from "react";

type ChatResponse = {
  answer: string;
  intent: string;
  product: string | null;
  quantity: number | null;
  interpreter: "llm" | "fallback";
};

type Message = {
  id: number;
  role: "user" | "assistant";
  text: string;
  interpreter?: ChatResponse["interpreter"];
};

type Theme = "light" | "dark";

const SUGGESTIONS = [
  "Tem quantas maçãs?",
  "Quanto custa a banana?",
  "Qual a mais barata?",
  "O que está acabando?",
  "Quantas frutas no total?",
];

function getInitialTheme(): Theme {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      text: "Oi! Pergunte sobre quantidade, preço, o que está acabando ou o total do estoque. \u{1F34E}",
      interpreter: "fallback",
    },
  ]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isLoading) {
      return;
    }

    const userMessageId = Date.now();
    setMessages((current) => [
      ...current,
      { id: userMessageId, role: "user", text: trimmed },
    ]);
    setQuestion("");
    setIsLoading(true);
    setError("");

    try {
      const request = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!request.ok) {
        throw new Error("Nao foi possivel consultar o estoque.");
      }

      const data = (await request.json()) as ChatResponse;
      setMessages((current) => [
        ...current,
        {
          id: userMessageId + 1,
          role: "assistant",
          text: data.answer,
          interpreter: data.interpreter,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <main className="app-shell">
      <div className="orb orb-1" aria-hidden="true" />
      <div className="orb orb-2" aria-hidden="true" />
      <div className="orb orb-3" aria-hidden="true" />

      <section className="chat-card">
        <header className="chat-header">
          <div className="brand-mark" aria-hidden="true">
            {"\u{1F34F}"}
          </div>
          <div className="brand-text">
            <h1>Estoque · AI</h1>
            <span className="brand-status">
              <i className="status-dot" aria-hidden="true" />
              Assistente online
            </span>
          </div>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((value) => (value === "dark" ? "light" : "dark"))}
            aria-label={theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro"}
            title="Alternar tema"
          >
            {theme === "dark" ? "☀️" : "\u{1F319}"}
          </button>
        </header>

        <div className="chat-window" aria-live="polite">
          {messages.map((message) => (
            <div className={`message-row ${message.role}`} key={message.id}>
              <div className="avatar" aria-hidden="true">
                {message.role === "user" ? "\u{1F9D1}" : "\u{1F916}"}
              </div>
              <div className="bubble">
                <p>{message.text}</p>
                {message.role === "assistant" && message.interpreter ? (
                  <span className={`badge ${message.interpreter}`}>
                    {message.interpreter === "llm" ? "\u{1F9E0} LLM local" : "⚙️ Fallback"}
                  </span>
                ) : null}
              </div>
            </div>
          ))}

          {isLoading ? (
            <div className="message-row assistant">
              <div className="avatar" aria-hidden="true">
                {"\u{1F916}"}
              </div>
              <div className="bubble typing" aria-label="Consultando estoque">
                <span />
                <span />
                <span />
              </div>
            </div>
          ) : null}

          <div ref={chatEndRef} />
        </div>

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            send(question);
          }}
        >
          <div className="chips">
            {SUGGESTIONS.map((suggestion) => (
              <button
                type="button"
                className="chip"
                key={suggestion}
                disabled={isLoading}
                onClick={() => send(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>

          <label className="visually-hidden" htmlFor="question">
            Pergunta
          </label>
          <div className="input-row">
            <input
              id="question"
              ref={inputRef}
              autoComplete="off"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Pergunte sobre o estoque..."
              type="text"
              value={question}
            />
            <button
              className="send-btn"
              disabled={isLoading}
              type="submit"
              aria-label="Enviar pergunta"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
          </div>

          {error ? <p className="feedback error">{error}</p> : null}
        </form>
      </section>
    </main>
  );
}

export default App;
