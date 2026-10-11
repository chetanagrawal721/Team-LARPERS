import { useEffect, useState } from "react";

export default function App() {
  const [health, setHealth] = useState("checking…");
  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((r) => r.json())
      .then((j) => setHealth(j.status))
      .catch(() => setHealth("offline"));
  }, []);
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-accent">🔏 SEALGATE</h1>
      <p>Gateway: {health}</p>
    </div>
  );
}
