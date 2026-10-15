import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [online, setOnline] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      await api.health();
      setOnline(true);
      setTasks(await api.list());
      setError("");
    } catch {
      setOnline(false);
      setError("Cannot reach the API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function run(action) {
    try {
      await action();
      setTasks(await api.list());
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    const value = title.trim();
    if (!value) return;
    run(async () => {
      await api.create(value);
      setTitle("");
    });
  }

  const remaining = tasks.filter((t) => !t.done).length;

  return (
    <main className="card">
      <header className="header">
        <h1>Tasks</h1>
        <span className={`pill ${online === null ? "" : online ? "ok" : "bad"}`}>
          {online === null ? "checking…" : online ? "API online" : "API offline"}
        </span>
      </header>

      <form onSubmit={onSubmit} className="form">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          maxLength={200}
          autoFocus
        />
        <button type="submit" disabled={!title.trim()}>
          Add
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : tasks.length === 0 ? (
        <p className="muted">No tasks yet. Add your first one above.</p>
      ) : (
        <ul className="list">
          {tasks.map((t) => (
            <li key={t.id} className={t.done ? "done" : ""}>
              <label>
                <input
                  type="checkbox"
                  checked={t.done}
                  onChange={() => run(() => api.toggle(t.id, !t.done))}
                />
                <span>{t.title}</span>
              </label>
              <button className="link" onClick={() => run(() => api.remove(t.id))} aria-label="Delete">
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {tasks.length > 0 && <p className="muted footer">{remaining} left</p>}
    </main>
  );
}
