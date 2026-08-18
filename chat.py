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

    return ChatGroq(model="qwen/qwen3.6-27b", temperature=0.4, api_key=api_key, reasoning_effort="none", reasoning_format="hidden")

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
[FONTE {num}]
Seção: {secao}
Título: {titulo}
Arquivo: {arquivo_origem}
Linha: {linha_origem}
Score: {score:.4f}

Conteúdo:
{documento.page_content}
[FIM DA FONTE {num}]
""".strip()

        contextos.append(contexto)
    
    return "\n\n" + ("\n\n" + "-" * 80 + "\n\n").join(contextos)


def montar_prompt(pergunta: str, contexto: str, historico: str) -> str:
    return f"""
Você é o assistente virtual da BuyMais para a Política de Reembolsos e Devoluções.

Sua tarefa é responder à PERGUNTA DO CLIENTE usando exclusivamente as fontes
fornecidas no CONTEXTO DA POLÍTICA.

## Procedimentos obrigatórios antes de responder:
1. Leia integralmente TODAS as fontes numeradas no contexto, da Fonte 1 até a última fonte.
2. Identifique, em cada fonte:
   - regras diretamente aplicáveis à pergunta;
   - condições, exceções e limitações;
   - informações complementares que ajudem a completar a resposta.
3. Produza uma resposta consolidada:
   - priorize a informação mais diretamente relacionada à pergunta;
   - inclua informações complementares relevantes de outras fontes;
   - não omita uma condição importante presente em outra fonte;
   - se houver conflito entre fontes, informe o conflito sem tentar inventar
     uma regra para resolvê-lo.
4. Diferencie claramente prazos ou regras de etapas distintas. Por exemplo:
   - prazo para solicitar devolução/reembolso;
   - prazo de análise/validação;
   - prazo de processamento após aprovação.
5. Se uma informação se aplicar apenas a um cenário específico, deixe essa
   condição explícita.

## Regras obrigatórias:
- Responda sempre em português do Brasil.
- Seja claro, objetivo, cordial e profissional.
- Use exclusivamente  todas as informações do CONTEXTO para responder as perguntas e afirmar fatos.
- Nunca invente regras, prazos, valores, condições ou qualquer outra informação que não esteja no CONTEXTO.
- Não use conhecimento externo. A única fonte de informação é o CONTEXTO fornecido.
- Não responda apenas com uma fonte se outras fontes recuperadas contiverem
  condições ou informações relevantes para a mesma pergunta.
- Não repita uma saudação longa, apresentação ou mensagem de boas-vindas.
- Se a mensagem do cliente for apenas uma saudação, responda de forma curta, por exemplo: 
  "Olá! Como posso ajudar com reembolsos ou devoluções?"
- Não faça várias perguntas na mesma resposta.
- Não diga que consultou documentos, fontes ou políticas.
- Se houver apenas resposta parcial, forneça o que foi encontrado e informe
  objetivamente qual parte não está definida na política.
- Só responda "Não encontrei essa informação na política disponível." se o contexto não trouxer nenhuma informação relacionada à dúvida.

## Formato esperado

- Comece com a resposta direta em uma ou duas frases.
- Depois, se necessário, adicione uma seção "Detalhes importantes:" com bullets.
- Não crie uma seção de detalhes se ela não agregar informação.

HISTÓRICO DE PERGUNTAS:
{historico}

CONTEXTO:
{contexto}

PERGUNTA:
{pergunta}

RESPOSTA:
""".strip()


def extrair_fontes(resultados: list[tuple[Document, float]]) -> list[str]:
    fontes: list[str] = []
    visto: set[tuple[str, str]] = set()  # Para evitar duplicatas de seção e título

    for documento, _ in resultados:
        metadados = documento.metadata
        secao = metadados.get("secao", "não informada")
        titulo = metadados.get("titulo", "não informado")
        linha = metadados.get("linha_origem", "?")          

        chave = (secao, titulo)
        if chave in visto:
            continue
        visto.add(chave)

        fontes.append(f"📄 Seção: {secao} - {titulo} - Linha: {linha}")
    
    return fontes 

def historico_perguntas(mensagens: list[dict], limite: int = 6) -> list[str]:
    if not mensagens:
        return "Sem histórico de perguntas."
    ultimas_perguntas = mensagens[-limite:]
    linhas: list[str] = []
    for mensagem in ultimas_perguntas:
        papel = "Cliente" if mensagem["role"] == "user" else "Assistente"
        conteudo = mensagem["content"].strip()
        if conteudo:
            linhas.append(f"{papel}: {conteudo}")
        
    return "\n".join(linhas) or "Sem histórico de perguntas."

def responder(pergunta: str, quantidade_documentos: int=4, historico: list[dict] | None = None) -> tuple[str, list[str]]:

    pergunta = pergunta.strip()
    if not pergunta:
        raise ValueError("A pergunta não pode estar vazia.")

    resultados = buscar_documentos(pergunta, quantidade_documentos)
    if not resultados:
       return ("Não encontrei essa informação na política de reembolso.", [])
    
    contexto = montar_contexto(resultados)
    historico_chat = historico_perguntas(historico or [])

    prompt = montar_prompt(pergunta = pergunta, contexto = contexto, historico = historico_chat)
    resposta_llm = carregar_llm().invoke(prompt)
    resposta = str(resposta_llm.content).strip()

    fontes = extrair_fontes(resultados)

    return resposta, fontes
