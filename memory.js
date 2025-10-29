// memory.js
import express from "express";
import fs from "fs";
import cors from "cors";

const app = express();
app.use(express.json());
app.use(cors());

const MEMORY_FILE = "memory.json";

// cria o arquivo se não existir
if (!fs.existsSync(MEMORY_FILE)) fs.writeFileSync(MEMORY_FILE, JSON.stringify([]));

// registrar nova lembrança
app.post("/registrar", (req, res) => {
  const { role, content } = req.body;
  const data = JSON.parse(fs.readFileSync(MEMORY_FILE, "utf8"));
  data.push({ role, content, date: new Date().toISOString() });
  fs.writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2));
  res.json({ status: "ok" });
});

// consultar lembranças
app.get("/lembrar", (req, res) => {
  const { mensagem } = req.query;
  const data = JSON.parse(fs.readFileSync(MEMORY_FILE, "utf8"));
  const relevantes = data.filter(
    (m) => m.content.toLowerCase().includes(mensagem.toLowerCase())
  );
  res.json(relevantes.slice(-5)); // devolve as 5 mais recentes
});

app.listen(3000, () => console.log("🧠 Servidor de memória ativo na porta 3000"));
