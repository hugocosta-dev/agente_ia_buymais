import os, re
from functools import lru_cache
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from criar_indice_vetorial import criar_indice_vetorial, INDEX_PATH, EMBEDDING_MODEL


load_dotenv()

DOCUMENTO = "Política de Reembolsos e Devoluções - BuyMais"

# Carrega o modelo de embeddings apenas uma vez.
@lru_cache(maxsize=1)
def carregar_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Cria o índice vetorial e carrega o vectorstore apenas uma vez.
@lru_cache(maxsize=1)
def carregar_vectorstore()-> FAISS:

    if not INDEX_PATH.exists():
        print(f"⚠️ Índice não encontrado em: {INDEX_PATH}. Criando índice vetorial...")
    criar_indice_vetorial()

    return FAISS.load_local(str(INDEX_PATH),carregar_embeddings(), allow_dangerous_deserialization=True)

# Carrega o modelo LLM apenas uma vez.
@lru_cache(maxsize=1)
def carregar_llm()-> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("A chave de API no arquivo .env não foi encontrada.")

    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=api_key)

def buscar_documentos(pergunta: str, quantidade: int = 4) -> list[tuple[Document, float]]:
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
    if not resultados:
        return ""
    
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
    
    return "\n\n" + ("\n\n" + "-" * 80 + "\n\n").join(contextos)


def montar_prompt(pergunta: str, contexto: str) -> str:
    return f"""
Você é o assistente da BuyMais para a Política de Reembolsos e Devoluções.

Regras:
- Responda sempre em português do Brasil.
- Seja objetivo, cordial e profissional.
- Use exclusivamente as informações do CONTEXTO para responder dúvidas sobre reembolsos, devoluções, prazos, pagamentos e condições.
- Nunca invente regras, prazos, valores ou condições.
- Não use conhecimento externo. A única fonte de informação é o CONTEXTO fornecido.
- Não repita uma saudação longa, apresentação ou mensagem de boas-vindas.
- Se a mensagem do cliente for apenas uma saudação, responda de forma curta, por exemplo: "Olá! Como posso ajudar com reembolsos ou devoluções?"
- Não faça várias perguntas na mesma resposta.
- Não diga que consultou documentos, fontes ou políticas.
- Se houver informação parcial, explique claramente a condição aplicável.
- Só responda "Não encontrei essa informação na política disponível." se o contexto não trouxer nenhuma informação relacionada à dúvida.

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
        secao = metadados.get("secao", "não informada")
        titulo = metadados.get("titulo", "não informado")
        linha = metadados.get("linha_origem", "?")
          
        
        fontes.append(f"📄 Seção: {secao} - {titulo} - Linha: {linha}")
    
    return fontes 

def responder(pergunta: str, quantidade_documentos: int=4) -> tuple[str, list[str]]:

    pergunta = pergunta.strip()
    if not pergunta:
        raise ValueError("A pergunta não pode estar vazia.")

    resultados = buscar_documentos(pergunta, quantidade_documentos)
    if not resultados:
       return ("Não encontrei essa informação na política de reembolso.", [])
    
    contexto = montar_contexto(resultados)

    # Diagnóstico temporário
    print("\n" + "=" * 80)
    print(f"PERGUNTA: {pergunta}")

    for documento, score in resultados:
        print(f"\nSCORE: {score:.4f}")
        print(documento.page_content)

    print("\nCONTEXTO ENVIADO:")
    print(contexto)
    print("=" * 80)

    prompt = montar_prompt(pergunta, contexto)
    resposta_llm = carregar_llm().invoke(prompt)
    resposta = str(resposta_llm.content).strip()

    print(f"\nRESPOSTA DA GROQ: {resposta!r}\n")

    fontes = extrair_fontes(resultados)

    return resposta, fontes
