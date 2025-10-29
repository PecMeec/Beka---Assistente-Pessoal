# server.py
import os
import re
import sqlite3
import datetime
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import minha_ia
import pandas as pd  # só se for usar upload de planilha

load_dotenv()

APP_PORT = int(os.getenv("APP_PORT", "5000"))
STATIC_FOLDER = os.path.join(os.getcwd(), "static")
DB_FILE = os.getenv("DB_FILE", "backup.db")
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="/static")
CORS(app, resources={r"/*": {"origins": "*"}})

# ----------------- DB helpers -----------------
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS conversas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        content TEXT,
        created_at TEXT
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS tecnicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estado TEXT,
        nome TEXT,
        cpf TEXT,
        rg TEXT,
        telefone TEXT,
        outros TEXT,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def save_conversa(role, content):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO conversas (role, content, created_at) VALUES (?, ?, ?)",
              (role, content, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def insert_tecnico(estado, nome, cpf=None, rg=None, telefone=None, outros=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO tecnicos (estado, nome, cpf, rg, telefone, outros, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (estado, nome, cpf, rg, telefone, outros, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def query_tecnicos_estado(estado, limit=500):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome, cpf, rg, telefone, outros, created_at FROM tecnicos WHERE estado = ? ORDER BY id DESC LIMIT ?", (estado, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_tecnico_by_name(nome):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tecnicos WHERE LOWER(nome) = LOWER(?)", (nome.strip(),))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted

def get_recent_conversation(limit=20):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role, content FROM conversas ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    # return as list oldest->newest
    return [{"role": r[0], "content": r[1]} for r in rows[::-1]]

init_db()

# ----------------- Parsing helpers -----------------
CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
TEL_RE = re.compile(r"(\(?\d{2,3}\)?\s?\d{4,5}[-\s]?\d{4})")
PLACA_RE = re.compile(r"\b[A-Z]{1,3}-?\d{1,4}[A-Z]{0,2}\b", re.IGNORECASE)

def detect_estado(text):
    # procura "DE RJ" ou "RJ" isolado depois de 'TÉCNICOS' / 'DADOS'
    m = re.search(r"TECNIC?OS?.*DE\s+([A-Za-z]{1,3})", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m2 = re.search(r"DADOS.*DE\s+([A-Za-z]{1,3})", text, re.IGNORECASE)
    if m2:
        return m2.group(1).upper()
    # procura sigla isolada
    m3 = re.search(r"\b(RJ|SP|MG|BA|PR|RS|SC|DF|GO|ES|PE|CE|PB|SE|AL|PI|MA)\b", text, re.IGNORECASE)
    if m3:
        return m3.group(1).upper()
    return None

def split_records(block):
    # tenta dividir em linhas por ; ou \n
    if not block:
        return []
    if ";" in block:
        parts = [p.strip() for p in block.split(";") if p.strip()]
        return parts
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if lines:
        return lines
    # fallback: split by comma but careful
    parts = [p.strip() for p in re.split(r",\s*(?=[A-Z])", block) if p.strip()]
    return parts

def parse_technician(line):
    # heurística simples
    nome = None
    cpf = None
    telefone = None
    rg = None

    cpf_m = CPF_RE.search(line)
    if cpf_m: cpf = cpf_m.group(0)

    tel_m = TEL_RE.search(line)
    if tel_m: telefone = tel_m.group(1)

    rg_m = re.search(r"\bRG[:\s]*([\d\.\-]+)\b", line, re.IGNORECASE)
    if rg_m: rg = rg_m.group(1)

    # tentative name: text before CPF or before 'CPF' literal or before phone
    cut_pos = None
    mcpf = re.search(r"\bCPF\b", line, re.IGNORECASE)
    if mcpf:
        cut_pos = mcpf.start()
    elif cpf_m:
        cut_pos = cpf_m.start()
    elif tel_m:
        cut_pos = tel_m.start()
    if cut_pos:
        cand = line[:cut_pos].strip().strip(":,-")
    else:
        # try take up to first digit sequence
        cand = re.split(r"\d", line, 1)[0].strip().strip(":,-")
    # cleanup known labels
    cand = re.sub(r"\b(DADOS|TECNICOS|TÉCNICOS|DE|DO|DOS)\b", "", cand, flags=re.IGNORECASE).strip()
    if cand:
        nome = cand
    outros = line
    return {"nome": nome, "cpf": cpf, "rg": rg, "telefone": telefone, "outros": outros}

# ----------------- Endpoints -----------------
@app.route("/")
def index():
    return send_from_directory(STATIC_FOLDER, "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_msg = (data.get("message") or "").strip()
        if not user_msg:
            return jsonify({"reply": "⚠️ Mensagem vazia"}), 400

        # Save user message to history
        save_conversa("user", user_msg)

        low = user_msg.lower()

        # ----- DELETE command: 'DELETE <nome>' (case-insensitive) -----
        # Accept "delete:" or "delete " at start
        mdel = re.match(r"^\s*delete[:\s]+(.+)$", user_msg, re.IGNORECASE)
        if mdel:
            target = mdel.group(1).strip()
            if not target:
                reply = "⚠️ Informe o nome para deletar: exemplo 'DELETE Maicon'."
            else:
                deleted = delete_tecnico_by_name(target)
                if deleted > 0:
                    reply = f"✅ Removido(s) {deleted} registro(s) com nome '{target}'."
                else:
                    reply = f"❌ Nenhum técnico chamado '{target}' encontrado no banco."
            save_conversa("assistant", reply)
            return jsonify({"reply": reply})

        # ----- SAVE command: "guarde no banco:" or "guardar no banco" -----
        if re.search(r"\bguarde\b.*\bbanco\b", low) or low.startswith("guarde no banco") or low.startswith("guardar no banco") or low.startswith("guardar:"):
            # detect state
            estado = detect_estado(user_msg) or "DESCONHECIDO"
            # extract data part after ':' if present
            if ":" in user_msg:
                after = user_msg.split(":", 1)[1].strip()
            else:
                # take after 'banco'
                parts = re.split(r"\bbanco\b", user_msg, flags=re.IGNORECASE)
                after = parts[1].strip() if len(parts) > 1 else ""
            if not after:
                reply = "⚠️ Não encontrei dados após o comando. Use: 'Guarde no banco: <dados; separados; por ;>'."
                save_conversa("assistant", reply)
                return jsonify({"reply": reply})

            regs = split_records(after)
            inserted = 0
            examples = []
            for r in regs:
                parsed = parse_technician(r)
                # Only insert if has a name or CPF
                if parsed.get("nome") or parsed.get("cpf"):
                    insert_tecnico(estado, parsed.get("nome") or "(sem nome)", parsed.get("cpf"), parsed.get("rg"), parsed.get("telefone"), parsed.get("outros"))
                    inserted += 1
                    if len(examples) < 5:
                        examples.append(parsed)
            reply = f"✅ Salvos {inserted} registro(s) para {estado}."
            if examples:
                reply += "\nExemplo(s):\n" + "\n".join([f"- {e.get('nome') or '(sem nome)'} | CPF: {e.get('cpf') or '-'} | Tel: {e.get('telefone') or '-'}" for e in examples])
            save_conversa("assistant", reply)
            return jsonify({"reply": reply})

        # ----- QUERY command: 'técnicos de RJ' or 'tecnicos de RJ' -----
        mq = re.search(r"\b(tecnic|t[eé]cnico|t[eé]cnicos)\b.*\bde\s+([A-Za-z]{1,3})\b", user_msg, re.IGNORECASE)
        if mq:
            estado = mq.group(2).upper()
            rows = query_tecnicos_estado(estado, limit=500)
            if not rows:
                reply = f"❌ Não encontrei técnicos cadastrados para {estado}."
                save_conversa("assistant", reply)
                return jsonify({"reply": reply})
            # format nicely
            lines = [f"📋 Técnicos de {estado} — total: {len(rows)}\n"]
            for i, r in enumerate(rows[:200], start=1):
                _id, nome, cpf, rg, tel, outros, created = r
                lines.append(f"{i}. {nome}")
                if cpf: lines.append(f"   • CPF: {cpf}")
                if rg: lines.append(f"   • RG: {rg}")
                if tel: lines.append(f"   • Tel: {tel}")
                # don't overload, but show 'outros' truncated
                if outros:
                    snippet = (outros[:160] + "...") if len(outros) > 160 else outros
                    lines.append(f"   • Obs: {snippet}")
                lines.append("")  # blank line
            reply = "\n".join(lines)
            save_conversa("assistant", reply)
            return jsonify({"reply": reply})

        # ----- otherwise: forward to LM Studio (conversa normal) -----
        # build history to provide context (last 12 messages)
        recent = get_recent_conversation(limit=12)
        # convert to LM messages format
        lm_history = []
        for m in recent:
            role = m["role"]
            content = m["content"]
            # keep roles as user/assistant; system message injected inside minha_ia
            lm_history.append({"role": "user" if role == "user" else "assistant", "content": content})
        try:
            bot_reply = minha_ia.conversar_com_ia(user_msg, lm_history, timeout=60)
        except Exception as e:
            bot_reply = f"❌ Erro ao conectar ao modelo local: {e}"

        # safety fallback
        if not bot_reply:
            bot_reply = "⚠️ Ocorreu um problema ao obter resposta da IA."

        save_conversa("assistant", bot_reply)
        return jsonify({"reply": bot_reply})

    except Exception as e:
        # Always return JSON so front won't break
        return jsonify({"reply": f"❌ Erro interno no servidor: {str(e)}"}), 500

# Upload endpoint (planilhas)
@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return jsonify({"reply": "❌ Nenhum arquivo enviado"}), 400
        f = request.files["file"]
        if f.filename == "":
            return jsonify({"reply": "❌ Arquivo sem nome"}), 400
        path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(path)
        # try to read with pandas if xls/xlsx/csv
        try:
            if f.filename.lower().endswith((".xls", ".xlsx", ".xlsm")):
                # xlrd/openpyxl may fail on damaged files - catch exceptions
                df = pd.read_excel(path, engine="openpyxl")
            elif f.filename.lower().endswith(".csv"):
                df = pd.read_csv(path)
            else:
                return jsonify({"reply": f"✅ Arquivo salvo: {f.filename} (não é planilha ou não foi processada)."})
            # do not auto-insert huge datasets — just show summary
            nrows, ncols = df.shape
            sample = df.head(5).to_dict(orient="records")
            return jsonify({"reply": f"✅ Planilha '{f.filename}' recebida: {nrows} linhas x {ncols} colunas. Exemplo (até 5): {sample}"})
        except Exception as e:
            return jsonify({"reply": f"⚠️ Erro ao ler planilha: {str(e)}. Você pode enviar os técnicos manualmente com 'Guarde no banco:'."}), 500
    except Exception as e:
        return jsonify({"reply": f"❌ Erro no upload: {str(e)}"}), 500

# Simple search endpoint
@app.route("/technicians/search", methods=["GET"])
def tech_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": []})
    estado = q.upper()
    rows = query_tecnicos_estado(estado, limit=500)
    results = []
    for r in rows:
        _id, nome, cpf, rg, tel, outros, created = r
        results.append({"id": _id, "nome": nome, "cpf": cpf, "rg": rg, "telefone": tel, "outros": outros, "created_at": created})
    return jsonify({"results": results})

if __name__ == "__main__":
    print(f"Servidor rodando em http://127.0.0.1:{APP_PORT}  — DB: {DB_FILE}")
    app.run(host="127.0.0.1", port=APP_PORT, debug=True)

