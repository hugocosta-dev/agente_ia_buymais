from pathlib import Path
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

CSV_PATH = "./documentos/politica_reembolsos_buymais.csv"
INDEX_PATH = "./indice/db_faiss"

def main():
    csv_file = Path(CSV_PATH)
    if not csv_file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {CSV_PATH}")

    # Carrega o arquivo CSV
    loader = CSVLoader(
        file_path=CSV_PATH,
        encoding="utf-8-sig",
        csv_args={
            "delimiter": ",",
            "quotechar": '"',
        },
    )

    documents = loader.load()

    print(f"Documentos carregados: {len(documents)}")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    print("Gerando embeddings...")

    vectorstore = FAISS.from_documents(documents,embeddings,)
    Path("indice").mkdir(exist_ok=True)
    vectorstore.save_local(INDEX_PATH)

    print(f"Índice criado com sucesso em: {INDEX_PATH}")


if __name__ == "__main__":
    main()