import csv
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

CSV_PATH = Path("./documentos/politica_reembolsos_buymais.csv")
INDEX_PATH = Path("./indice/db_faiss")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def carregar_documentos() -> list[Document]:
    documentos = list[Document]()

    with CSV_PATH.open( "r", encoding="utf-8-sig", newline="",) as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=",", quotechar='"')
        colunas_esperadas = {"id", "secao", "titulo", "conteudo", "empresa"}
        colunas_csv = set(leitor.fieldnames or [])
        colunas_ausentes = colunas_esperadas - colunas_csv
        if colunas_ausentes:
            raise ValueError(f"Colunas ausentes no CSV: {', '.join(sorted(colunas_ausentes))}")
        
        for num, linha in enumerate(leitor, start=2): # Começa a contagem a partir da linha 2 (após o cabeçalho)
            titulo = (linha.get("titulo") or "").strip()
            conteudo = (linha.get("conteudo") or "").strip()
            secao = (linha.get("secao") or "").strip()
            empresa = (linha.get("empresa") or "").strip()
            id = (linha.get("id") or "").strip()

            if not titulo or not conteudo:
                print(f"Aviso: Linha {num} ignorada devido a título ou conteúdo ausente.")
                continue

            texto = f'''
            Seção: {secao}
Título: {titulo}

{conteudo}    
'''.strip()

            documento = Document(page_content=texto, 
                    metadata={
                    "id": id,
                    "secao": secao,
                    "titulo": titulo,
                    "empresa": empresa,
                    "arquivo_origem": CSV_PATH.name,
                    "linha_origem": num
                    }
                )
            documentos.append(documento)
        print(f"Total de documentos carregados: {len(documentos)}")
    return documentos


def criar_indice_vetorial() -> None:

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {CSV_PATH}")

    documents = carregar_documentos()

    if not documents:
        raise ValueError("Nenhum documento foi carregado do CSV.")
    
    print(f"#{len(documents)} Documento(s) OK\n")
    print(f"Carregando modelo de embeddings: {EMBEDDING_MODEL}...\n")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print("Criando índice vetorial...\n")
    
    vectorstore = FAISS.from_documents(documents,embeddings,)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_PATH))

    print(f"Índice criado com sucesso em: {INDEX_PATH}")

if __name__ == "__main__":
    criar_indice_vetorial()
