# 🤖 Agente de Reembolsos BuyMais

Agente desenvolvido em **Python** e **Streamlit** para responder perguntas sobre a política de reembolsos, devoluções e trocas da BuyMais.

O projeto utiliza uma arquitetura **RAG — Retrieval-Augmented Generation**. O conteúdo da política é carregado a partir de um arquivo CSV, transformado em embeddings e armazenado em um índice vetorial FAISS. Quando o usuário faz uma pergunta, os trechos mais relevantes são recuperados e enviados ao modelo de linguagem para gerar a resposta.

> Este projeto utiliza uma política documental fictícia criada com ajuda de IA e possui finalidade educativa.

---

## 📌 Funcionalidades

- 💬 Interface de chat com Streamlit
- 📄 Leitura da política a partir de arquivo CSV
- 🔎 Busca semântica utilizando embeddings
- 🧠 Respostas geradas por modelo Llama através da Groq
- 🗂️ Armazenamento local do índice vetorial com FAISS
- 📚 Exibição das fontes consultadas
- 🔐 Uso de variáveis de ambiente para armazenar a chave da API
- ⚡ Cache dos modelos e do índice para evitar carregamentos repetidos

---

## 🛠️ Tecnologias utilizadas

- Python 3.10+
- [Streamlit](https://streamlit.io/)
- [LangChain](https://www.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Hugging Face Sentence Transformers](https://huggingface.co/sentence-transformers)
- [Groq](https://groq.com/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

Principais bibliotecas Python:

- `streamlit`
- `langchain`
- `langchain-community`
- `langchain-core`
- `langchain-groq`
- `langchain-huggingface`
- `faiss-cpu`
- `sentence-transformers`
- `python-dotenv`

---

## 🧱 Arquitetura

O fluxo principal da aplicação é:

```text
Arquivo CSV
    ↓
Document
    ↓
Embeddings
    ↓
Índice FAISS
    ↓
Pergunta do usuário
    ↓
Busca semântica
    ↓
Contexto recuperado
    ↓
Modelo LLM da Groq
    ↓
Resposta com fontes
```

---

## 📁 Estrutura do projeto

```text
agente_ia_buymais/
│
├── app.py
├── chat.py
├── criar_indice_vetorial.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── documentos/
│   └── politica_reembolsos_buymais.csv
│
└── indice/
    └── db_faiss/
        ├── index.faiss
        └── index.pkl
```

### Principais arquivos e funções

| Arquivo | Função |
|---|---|
| `criar_indice_vetorial.py` | Lê o CSV e cria o índice FAISS |
| `chat.py` | Realiza a busca semântica e consulta o modelo LLM |
| `app.py` | Contém a interface do chat em Streamlit |
| `politica_reembolsos_buymais.csv` | Base documental da política |
| `.env` | Armazena variáveis sensíveis |
| `indice/db_faiss/` | Armazena o índice vetorial gerado |

---

## ⚙️ Configuração

### 1. Clone o projeto

```bash
git clone https://github.com/seu-usuario/agente-ia-buymais.git
cd agente-ia-buymais
```

Ou faça o download do projeto e abra a pasta no terminal.

---

### 2. Crie um ambiente virtual

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate
```

#### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

Um exemplo de arquivo `requirements.txt`:

```txt
python-dotenv
streamlit
faiss-cpu
langchain
langchain-community
langchain-core
langchain-groq
langchain-huggingface
sentence-transformers

```

---

### 4. Configure o arquivo `.env`

Crie um arquivo chamado `.env` na raiz do projeto:

```env
GROQ_API_KEY=sua_chave_da_api_groq
```

A chave pode ser criada no painel da [Groq](https://console.groq.com/).

> Nunca compartilhe sua chave da Groq nem envie o arquivo `.env` para o GitHub.

---

## 📄 Formato do arquivo CSV

O arquivo contem as seguintes colunas:

```csv
id,secao,titulo,conteudo,empresa
1,1,Propósito,"Conteúdo da seção...",BuyMais
2,2,Escopo,"Conteúdo da seção...",BuyMais
3,3,"Princípios gerais","Conteúdo da seção...",BuyMais
```
Você pode adaptar o arquivo criar_indice_vetorial de acordo com as colunas do seu arquivo CSV

---

## 🧠 Criação do índice vetorial

Antes de executar a aplicação, crie o índice FAISS:

```bash
python criar_indice_vetorial.py
```

Esse processo realiza as seguintes etapas:

1. Verifica se o arquivo CSV existe;
2. Lê as linhas da política;
3. Converte cada linha em um objeto `Document`;
4. Gera embeddings usando o modelo:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

5. Cria o índice FAISS;
6. Salva o índice em:

```text
indice/db_faiss/
```

Sempre que o CSV for alterado, o índice deverá ser recriado.

Remova o indice antigo e recrie com os comandos:

### Windows PowerShell

```powershell
Remove-Item -Recurse -Force .\indice\db_faiss
python criar_indice_vetorial.py
```

### Linux ou macOS

```bash
rm -rf ./indice/db_faiss
python criar_indice_vetorial.py
```
---

Depois de criar o índice, execute:

```bash
streamlit run app.py
```

---

## 💬 Exemplos de perguntas

```text
Qual é o prazo para solicitar devolução por arrependimento?
```

```text
Qual é o prazo para reclamar de um produto incorreto?
```

```text
Quanto tempo demora para processar um reembolso aprovado?
```

```text
O que é considerado dano em trânsito?
```

```text
A política se aplica a compras feitas por canais não oficiais?
```

---

## 🔎 Como funciona a busca semântica

Quando o usuário envia uma pergunta, o agente:

1. Remove espaços desnecessários;
2. Converte a pergunta em um embedding;
3. Consulta o índice FAISS;
4. Recupera os documentos semanticamente mais próximos;
5. Monta o contexto com seção, título e conteúdo;
6. Envia o contexto ao modelo da Groq;
7. Exibe a resposta e as fontes consultadas.

A aplicação não envia necessariamente todo o CSV ao modelo. Ela recupera os documentos mais relacionados à pergunta.

---

Depois, reinicie a aplicação:

```bash
streamlit run app.py
```

---

## 🧪 Testando a busca semântica

Para testar perguntas específicas, recomenda-se utilizar perguntas com contexto claro:

```text
Quantos dias corridos o cliente tem para solicitar devolução por arrependimento?
```

```text
Qual é o prazo para comunicar um produto incorreto?
```

```text
Em quanto tempo um reembolso aprovado é processado?
```

Perguntas muito amplas podem estar relacionadas a mais de uma regra. Por exemplo, a palavra “prazo” pode se referir a:

- prazo para solicitar uma devolução;
- prazo para comunicar um problema na entrega;
- prazo para processar um reembolso aprovado.

---

## 🔒 Segurança

- Nunca publique a variável `GROQ_API_KEY`;
- Mantenha o arquivo `.env` fora do GitHub;
- Não compartilhe índices que contenham dados sensíveis;
- Não utilize `allow_dangerous_deserialization=True` com índices de origem desconhecida;
- Utilize dados fictícios ou anonimizados durante os testes;
- Evite exibir exceções detalhadas em ambiente de produção.

Exemplo de `.gitignore`:

```gitignore
.venv/
.env
__pycache__/
*.pyc
.streamlit/
```

Se o índice for necessário no deploy, ele deverá ser gerado durante o processo de publicação ou enviado para um local controlado.

---

## ☁️ Deploy

A aplicação pode ser hospedada em serviços compatíveis com aplicações Python, como:

- [Streamlit Community Cloud](https://streamlit.io/cloud)
- [Render](https://render.com/)
- VPS com Python e nginx
- Outros serviços que suportem aplicações Streamlit

### Comando de instalação

```bash
pip install -r requirements.txt
```

### Comando de execução

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

No painel do serviço de hospedagem, configure:

```env
GROQ_API_KEY=sua_chave_da_api_groq
```

Também confirme que o índice FAISS está disponível no caminho esperado:

```text
indice/db_faiss/
```

---

## 📄 Licença

Este projeto é de uso pessoal e educativo.

A política utilizada é fictícia e pode ser adaptada para estudos, prototipagem e demonstrações de aplicações com inteligência artificial.

---

## ✉️ Contato

Feito por **Hugo Costa**

📧 hugocosta.ti@gmail.com