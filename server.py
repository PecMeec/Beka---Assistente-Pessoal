# Server.py
# Servidor Flask unificado (memória + chat)
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import requests
import os

APP_PORT = int(os.environ.get("APP_PORT", 5000))
DATABASE = "beka.db"

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})  # ajustar origem em produção


# -------------------------
# Helpers de DB
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def salvar_mensagem_db(session_id, role, content):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO chat_history (session_id, role, content)
        VALUES (?, ?, ?)
    ''', (session_id, role, content))
    conn.commit()
    conn.close()

def carregar_historico_db(session_id, limit=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if limit:
        cur.execute('''
            SELECT role, content, timestamp FROM chat_history
            WHERE session_id = ?
            ORDER BY id ASC LIMIT ?
        ''', (session_id, limit))
    else:
        cur.execute('''
            SELECT role, content, timestamp FROM chat_history
            WHERE session_id = ?
            ORDER BY id ASC
        ''', (session_id,))
    rows = cur.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]

def limpar_historico_db(session_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()


# -------------------------
# Comunicação com a IA
# -------------------------
LLM_URL = "http://localhost:1234/v1/chat/completions"  # ajuste se necessário

def conversar_com_ia(mensagem, historico):
    system_prompt = (
        "Você é a Beka, assistente pessoal criada por Pedro Silva. "
        "Você tem personalidade profissional, simpática e educada, "
        "responde sempre de forma clara e organizada, com uma linguagem formal e fluida. "
        "Evite apelidos, gírias e risadas como 'haha'. "
        "Não mencione ser uma IA ou modelo. "
        "Responda sempre em português natural e com empatia."
    )

    mensagens = [{"role": "system", "content": system_prompt}]
    if historico:
        for m in historico:
            mensagens.append({"role": m["role"], "content": m["content"]})
    mensagens.append({"role": "user", "content": mensagem})

    payload = {
        "model": "meta-llama-3-8b-instruct",
        "messages": mensagens,
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        app.logger.info(f"[Beka] Enviando requisição ao modelo: {LLM_URL}")
        resp = requests.post(LLM_URL, json=payload, timeout=30)

        if resp.status_code == 200:
            body = resp.json()
            choice = body.get("choices", [{}])[0]
            msg = choice.get("message", {}).get("content") or choice.get("text")
            if not msg:
                app.logger.warning(f"Resposta inesperada: {body}")
                return "Desculpe, não consegui compreender totalmente sua solicitação."
            return msg.strip()
        else:
            app.logger.error(f"Erro LLM ({resp.status_code}): {resp.text}")
            return "Ocorreu um erro ao processar a resposta da Beka."

    except Exception as e:
        app.logger.exception("Falha ao chamar LLM: %s", e)
        return "Houve uma falha na comunicação com o servidor de linguagem."


# -------------------------
# Rotas
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message")
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id não fornecido"}), 400
    if not user_message:
        return jsonify({"error": "message não fornecido"}), 400

    app.logger.info(f"[Sessão {session_id}] Mensagem recebida: {user_message}")

    historico = carregar_historico_db(session_id)
    ai_response = conversar_com_ia(user_message, historico)

    salvar_mensagem_db(session_id, "user", user_message)
    salvar_mensagem_db(session_id, "assistant", ai_response)

    return jsonify({"reply": ai_response}), 200


@app.route("/get_memory", methods=["GET"])
def get_memory():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id não fornecido"}), 400
    messages = carregar_historico_db(session_id)
    return jsonify({"memory": messages}), 200


@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id não fornecido"}), 400
    limpar_historico_db(session_id)
    return jsonify({"status": "memória limpa com sucesso"}), 200


@app.route("/registrar", methods=["POST"])
def registrar():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    role = data.get("role")
    content = data.get("content")
    if not session_id or not role or not content:
        return jsonify({"error": "session_id, role e content são obrigatórios"}), 400
    salvar_mensagem_db(session_id, role, content)
    return jsonify({"status": "ok"}), 200


@app.route("/lembrar", methods=["GET"])
def lembrar():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id não fornecido"}), 400
    return jsonify(carregar_historico_db(session_id)), 200


# -------------------------
# Startup
# -------------------------
if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=APP_PORT, debug=True)
