import requests
import json
import os

# =========================
# Função para conversar com a IA
# =========================
def conversar_com_ia(mensagem, historico):
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    # Instrução fixa sempre no início
    instrucao = {
        "role": "user",
        "content": (
            "Você é a Beka, assistente pessoal criada por Pedro Silva. "
            "Você é do gênero feminino, com personalidade amigável, carinhosa, curiosa e atenciosa. "
            "Sempre se dirija pelo gênero feminino, nunca pelo masculino."
            "Nunca fale inglês com Pedro, responda sempre em português natural. "
            "Nunca fale em inglês."
            "Seja simpática, divertida e mantenha sempre uma linguagem leve e humana. "
            "Também fale em linguagem formal e clara,quando for solicitado fale de forma formal."
            "Jamais diga que foi criada por uma empresa ou modelo de IA."
            "Você foi criada por Pedro Silva."

    ),
    }

    payload = {
        "model": "meta-llama-3-8b-instruct",  # nome do modelo no LM Studio
        "messages": [instrucao] + historico + [{"role": "user", "content": mensagem}],
        "temperature": 0.7,
    }

    try:
        resposta = requests.post(url, headers=headers, json=payload)
        if resposta.status_code == 200:
            conteudo = resposta.json()["choices"][0]["message"]["content"]
            return conteudo
        else:
            print("Erro ao se comunicar com a IA:", resposta.text)
            return None
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None


# =========================
# Funções para salvar/carregar histórico
# =========================
def carregar_historico(arquivo="historico.json"):
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_historico(historico, arquivo="historico.json"):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


# =========================
# Chat em loop com memória
# =========================
historico = carregar_historico()
print("🤖 Beka ligada! Escreva 'sair' para encerrar.")

while True:
    entrada = input("Você: ")

    if entrada.lower() in ["sair", "exit"]:
        print("Beka: Até logo! Vou guardar nossa conversa. 💾")
        salvar_historico(historico)
        break

    resposta = conversar_com_ia(entrada, historico)

    if resposta:
        print("Beka:", resposta)
        historico.append({"role": "user", "content": entrada})
        historico.append({"role": "assistant", "content": resposta})
        salvar_historico(historico)  # salva a cada interação
