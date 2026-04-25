from dotenv import load_dotenv
load_dotenv()

from haystack.utils import Secret
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore

document_store = PgvectorDocumentStore(
    connection_string=Secret.from_env_var("DATABASE_URL"),
    embedding_dimension=768,
    vector_function="cosine_similarity"
)