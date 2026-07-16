import { FormEvent, useState } from "react";

type ChatResponse = {
  answer: string;
  product: string | null;
  quantity: number | null;
};

function App() {
  const [question, setQuestion] = useState("Tem quantas macas?");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!question.trim()) {
      setError("Digite uma pergunta sobre o estoque.");
      return;
    }

    setIsLoading(true);
    setError("");
    setResponse(null);

    try {
      const request = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!request.ok) {
        throw new Error("Nao foi possivel consultar o estoque.");
      }

      const data = (await request.json()) as ChatResponse;
      setResponse(data);
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

        {response ? (
          <section className="answer-panel" aria-live="polite">
            <span>Resposta</span>
            <p>{response.answer}</p>
          </section>
        ) : null}
      </section>
    </main>
  );
}

export default App;
