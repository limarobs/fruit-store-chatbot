import { FormEvent, useEffect, useRef, useState } from "react";

type ChatResponse = {
  answer: string;
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

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      text: "Oi! Pergunte sobre maca, banana, laranja, uva ou abacaxi.",
      interpreter: "fallback",
    },
  ]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!question.trim()) {
      setError("Digite uma pergunta sobre o estoque.");
      return;
    }

    const currentQuestion = question.trim();
    const userMessageId = Date.now();

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: userMessageId,
        role: "user",
        text: currentQuestion,
      },
    ]);
    setQuestion("");
    setIsLoading(true);
    setError("");

    try {
      const request = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: currentQuestion }),
      });

      if (!request.ok) {
        throw new Error("Nao foi possivel consultar o estoque.");
      }

      const data = (await request.json()) as ChatResponse;
      setMessages((currentMessages) => [
        ...currentMessages,
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
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <p className="eyebrow">Loja de frutas</p>
        <h1>Chatbot de estoque</h1>
        <p className="intro">
          Pergunte pela quantidade disponivel de maca, banana, laranja, uva ou
          abacaxi.
        </p>

        <section className="chat-window" aria-live="polite">
          {messages.map((message) => (
            <article
              className={`message-bubble ${message.role}`}
              key={message.id}
            >
              <span>{message.role === "user" ? "Voce" : "Assistente"}</span>
              <p>{message.text}</p>
              {message.role === "assistant" && message.interpreter ? (
                <strong>
                  {message.interpreter === "llm"
                    ? "LLM local"
                    : "Fallback local"}
                </strong>
              ) : null}
            </article>
          ))}

          {isLoading ? (
            <article className="message-bubble assistant">
              <span>Assistente</span>
              <p>Consultando estoque...</p>
            </article>
          ) : null}

          <div ref={chatEndRef} />
        </section>

        <form className="chat-form" onSubmit={handleSubmit}>
          <label htmlFor="question">Pergunta</label>
          <div className="input-row">
            <input
              id="question"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ex: Tem quantas macas?"
              type="text"
              value={question}
            />
            <button disabled={isLoading} type="submit">
              {isLoading ? "Consultando..." : "Perguntar"}
            </button>
          </div>
        </form>

        {error ? <p className="feedback error">{error}</p> : null}
      </section>
    </main>
  );
}

export default App;
