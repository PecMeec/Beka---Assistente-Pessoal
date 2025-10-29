# 🤖 BEKA — Assistente de Inteligência Artificial Pessoal

**BEKA** (Built Enhanced Knowledge Assistant) é uma inteligência artificial pessoal desenvolvida em **Python** e **JavaScript**, com integração ao **LM Studio** e ao modelo **LLaMA Instruction**.  
O objetivo do projeto é criar uma assistente capaz de compreender conversas, armazenar memórias e interagir com o usuário de forma natural, como um verdadeiro assistente pessoal de mesa.

---

## 🧠 Funcionalidades Principais

- 💬 **Compreensão de linguagem natural** — entende perguntas e comandos via texto.
- 🧍 **Memória local persistente** — armazena conversas e informações no banco de dados.
- ⚙️ **Integração com LM Studio (LLaMA)** — processamento de linguagem via modelo local.
- 🌐 **Interface Web** — comunicação entre backend (Python) e frontend (HTML + JS).
- 📁 **Banco de Dados Local (SQLite)** — histórico e dados do usuário.
- 🧩 **Arquitetura modular** — separação entre backend, frontend e scripts auxiliares.

---

## 🧩 Estrutura do Projeto

Beka/

├── beka_app.py # Aplicação principal (rotas e lógica)  
├── serve.py # Servidor Flask que integra o front com o LM Studio  
├── minha_ia.py # Núcleo da IA: processamento e respostas  
├── script.js # Lógica da interface e comunicação via API    
├── index.html # Página principal da interface web     
├── memory.js # Controle de memória do lado do cliente            
├── beka.db # Banco de dados local (SQLite)               
├── requirements.txt # Dependências do projeto         
├── .gitignore # Arquivos ignorados no versionamento           
└── README.md # Este arquivo 🙂


## ⚙️ Instalação e Execução

2️⃣ Criar ambiente virtual (opcional, mas recomendado)
python -m venv venv
venv\Scripts\activate     # Windows
# ou
source venv/bin/activate  # Linux/Mac

3️⃣ Instalar dependências
pip install -r requirements.txt
python serve.py
O servidor será executado localmente, e você poderá acessar a interface da BEKA pelo navegador, geralmente em:
👉 http://localhost:5000

🧩 Tecnologias Utilizadas
Categoria	Tecnologias
Backend	Python, Flask
IA	LM Studio, LLaMA Instruction
Frontend	HTML, CSS, JavaScript
Banco de Dados	SQLite
Outros	Node.js, JSON, API REST

🧠 Futuras Implementações
🔉 Integração com reconhecimento de voz (Speech-to-Text)

🗣️ Respostas faladas (Text-to-Speech)

🪄 Interface aprimorada com React ou Vue

☁️ Salvamento de memórias em nuvem

👨‍💻 Autor
Pedro Silva
Analista de Suporte & Desenvolvedor em Formação
💼 LinkedIn
💻 GitHub
✉️ Contato: ph6467788@gmail.com

📜 Licença
Este projeto é de uso para fins de estudo e desenvolvimento pessoal.
Está sob minha autoria e não autorizo sob nenhuma circustância a sua clonagem, cópia ou uso para outros propósitos, a não ser para evolução da Beka!

✨ "Toda grande inteligência começa com uma curiosidade bem alimentada."
