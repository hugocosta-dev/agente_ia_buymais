from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from criar_indice_vetorial import INDEX_PATH, EMBEDDING_MODEL


def testar_busca_semantica():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Índice FAISS não encontrado em: {INDEX_PATH}")
    print(f"Carregando índice vetorial: {INDEX_PATH}")

    vectorstore = FAISS.load_local(str(INDEX_PATH),embeddings, allow_dangerous_deserialization=True,)
    pergunta = "A política se aplica a compras feitas por canais não oficiais?"

    results = vectorstore.similarity_search(pergunta, k=3,)

    print(f"\nPergunta: {pergunta}\n")
    print("Resultados encontrados:\n")

    for num, document in enumerate(results, start=1):
        print(f"--- Resultado {num} ---")
        print(document.page_content)
        print(f"Metadados: {document.metadata}")
        print()

if __name__ == "__main__":
    testar_busca_semantica()