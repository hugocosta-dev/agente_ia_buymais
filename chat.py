import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from criar_indice_vetorial import INDEX_PATH, EMBEDDING_MODEL


load_dotenv()

DOCUMENTO = "politica_reembolsos_buymais.csv"

# Carrega o modelo de embeddings apenas uma vez.
@lru_cache(maxsize=1)
def carregar_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Carrega o vectorstore apenas uma vez.
@lru_cache(maxsize=1)
def carregar_vectorstore()-> FAISS:   
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Índice não encontrado em: {INDEX_PATH}.")

    return FAISS.load_local(str(INDEX_PATH),carregar_embeddings(), allow_dangerous_deserialization=True)

# Carrega o modelo LLM apenas uma vez.
@lru_cache(maxsize=1)
def carregar_llm()-> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("A chave de API no arquivo .env não foi encontrada.")

    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=api_key)


def buscar_documentos(pergunta: str, quantidade: int = 3) -> list[tuple[Document, float]]:
    pergunta = pergunta.strip()
    if not pergunta:
        raise ValueError("A pergunta não pode estar vazia.")
    
    vectorstore = carregar_vectorstore()
    resultados = vectorstore.similarity_search_with_score(pergunta,k=quantidade)

    print(f"\nPergunta: {pergunta}")
    print(f"Documentos recuperados: {len(resultados)}")

    for documento, score in resultados:
        metadados = documento.metadata
        print(f"- Seção: {metadados.get('secao', 'nao informada')} " 
              f"| Título: {metadados.get('titulo', 'nao informado')} "
              f"| Score: {score:.4f}")

    return resultados


def montar_contexto(resultados: list[tuple[Document, float]]) -> str:
    
    contextos: list[str] = []

    for num, (documento, score) in enumerate(resultados, start=1):
        metadados = documento.metadata
        secao = metadados.get("secao", "não informada")
        titulo = metadados.get("titulo", "não informado")
        arquivo_origem = metadados.get("arquivo_origem", DOCUMENTO)
        linha_origem = metadados.get("linha_origem", "não informada")

        contexto= f"""
[Fonte {num}]
Seção: {secao}
Título: {titulo}
Arquivo: {arquivo_origem}
Linha: {linha_origem}
Score: {score:.4f}]

Conteúdo:
{documento.page_content}
""".strip()

        contextos.append(contexto)

    if not contextos:
        return ""

    return "\n\n" + ("\n\n" + "-" * 80 + "\n\n").join(contextos)


def montar_prompt(pergunta: str, contexto: str) -> str:
    return f"""
Você é o agente de atendimento da BuyMais.

Responda à pergunta usando somente as informações do contexto.

Regras:
- Responda em português.
- Seja claro, objetivo e profissional.
- Não invente informações.
- Não use conhecimento externo.
- Se a resposta não estiver no contexto, responda:
  "Não encontrei essa informação na política disponível."

Contexto:
{contexto}

Pergunta:
{pergunta}

Resposta:
""".strip()


def extrair_fontes(resultados: list[tuple[Document, float]]) -> list[str]:
    fontes: list[str] = []

    for documento, _ in resultados:
        metadados = documento.metadata
        arquivo_origem = metadados.get("arquivo_origem", DOCUMENTO)
        arquivo = str(arquivo_origem).replace("\\", "/").split("/")[-1]

        if arquivo not in fontes:
            fontes.append(arquivo)
    
    return fontes


def responder(pergunta: str, quantidade_documentos: int=4) -> tuple[str, list[str]]:

    pergunta = pergunta.strip()
    if not pergunta:
        raise ValueError("A pergunta não pode estar vazia.")

    resultados = buscar_documentos(pergunta, quantidade_documentos)
    if not resultados:
       return ("Não encontrei essa informação na política de reembolso.", [])
    
    contexto = montar_contexto(resultados)
    prompt = montar_prompt(pergunta, contexto)
    resposta_llm = carregar_llm().invoke(prompt)
    resposta = str(resposta_llm.content).strip()
    fontes = extrair_fontes(resultados)

    return resposta, fontes
