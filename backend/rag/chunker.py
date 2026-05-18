from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_chunker():
    """
    Returns a text splitter configured for medical texts.
    Chunk size = 500, overlap = 100 as per requirements.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

def chunk_document(text: str) -> list[str]:
    """
    Chunks a single document text into smaller strings.
    """
    chunker = get_chunker()
    return chunker.split_text(text)
