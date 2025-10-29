# =============================================
# BEKA_APP.PY — Servidor Flask com memória persistente
# =============================================

from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

# Caminhos dos arquivos de memória
DB_PATH = "beka.db"
MEMORY_PATH = "memory.json"

# =============================================
# 🔧 Função para garantir que o banco exista
# =============================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# =============================================
# 💾 Salva uma nova entrada no banco
# =============================================
def save_to_db(role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO memory (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# =============================================
# 📤 Recupera as últimas mensagens do banco
# =============================================
def get_recent_from_db(limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM memory ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    messages = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    return messages

# =============================================
# 🔁 Sincroniza banco e JSON
# =============================================
def sync_memory():
    # Se não existir o banco, cria
    init_db()

    # Puxa do banco as últimas conversas
    db_messages = get_recent_from_db(limit=50)

    # Se o JSON não existir, cria novo
    if not os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump({"memory": db_messages}, f, indent=4, ensure_ascii=False)
        return db_messages

    # Lê o JSON existente
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"memory": []}

    # Se estiver vazio, atualiza com o conteúdo do banco
    if not data.get("memory"):
        data["memory"] = db_messages
    else:
        # Adiciona apenas as novas mensagens que ainda não estão no JSON
        existing = {(m["role"], m["content"]) for m in data["memory"]}
        for msg in db_messages:
            if (msg["role"], msg["content"]) not in existing:
                data["memory"].append(msg)

    # Salva o JSON sincronizado
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return data["memory"]

# =============================================
# 🧠 Rota para salvar mensagens (memória)
# =============================================
@app.route("/save_message", methods=["POST"])
def save_message():
    data = request.json
    role = data.get("role")
    content = data.get("content")

    if not role or not content:
        return jsonify({"error": "Campos 'role' e 'content' são obrigatórios"}), 400

    # Salva no banco
    save_to_db(role, content)

    # Sincroniza com JSON
    sync_memory()

    return jsonify({"status": "mensagem salva com sucesso"}), 200

# =============================================
# 📚 Rota para recuperar o histórico completo
# =============================================
@app.route("/get_memory", methods=["GET"])
def get_memory():
    messages = sync_memory()
    return jsonify({"memory": messages}), 200

# =============================================
# 🧹 Rota para limpar a memória (banco + JSON)
# =============================================
@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM memory")
    conn.commit()
    conn.close()

    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump({"memory": []}, f, indent=4, ensure_ascii=False)

    return jsonify({"status": "memória limpa com sucesso"}), 200

# =============================================
# 🔗 Rotas compatíveis com o server.py
# =============================================

@app.route("/lembrar", methods=["GET"])
def lembrar():
    """Retorna as memórias armazenadas"""
    messages = sync_memory()
    return jsonify(messages), 200

@app.route("/registrar", methods=["POST"])
def registrar():
    """Registra uma nova lembrança (igual a /save_message, mas compatível com o server.py)"""
    data = request.json
    role = data.get("role")
    content = data.get("content")
    if not role or not content:
        return jsonify({"error": "Campos 'role' e 'content' são obrigatórios"}), 400
    save_to_db(role, content)
    sync_memory()
    return jsonify({"status": "ok"}), 200


# =============================================
# 🚀 Inicialização
# =============================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    init_db()
    sync_memory()
    app.run(host="127.0.0.1", port=args.port, debug=True)

