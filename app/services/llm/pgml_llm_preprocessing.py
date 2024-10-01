from pgml import OpenSourceAI, Model, Pipeline, Collection
import openai
from pypdf import PdfReader
import os
from rich import print
from rich.progress import track


async def chat_flow():

    ll_name = ""
    document_name = "/Users/babawhizzo/Code/map_action_ml/ML-Deploy/test/test_llm/dummy.pdf"

    pipeline = Pipeline(
        "Main_Pipeline",
        {
            "body": {
                "splitter": {"model": "recursive_character"},
                "semantic_search": {
                    "model": "hkunlp/instructor-base",
                    "parameters": {
                        "instruction": "Represent the Wikipedia document for retrieval: ",
                    },
                },
            },
        },
    )

    conninfo = "postgres://root:postgresml@localhost:5433/postgresml"

    reader = PdfReader(document_name)
    num_pages = len(reader.pages)

    documents = []

    for page_number, page in track(enumerate(reader.pages)):
        documents.append(
            {"id": 1,
             "title": "Map Action text",
             "text": page.extract_text(),
             "page": page_number,
             "source": document_name}
        )

    collection_name = "MapActionManifesto"
    collection = Collection(collection_name, conninfo)

    await collection.add_pipeline(pipeline)

    await collection.upsert_documents(documents)

    return collection, pipeline
