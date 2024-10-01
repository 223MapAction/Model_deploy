import os
from ..llm.llm_preprocessing import chain_workflow


def contextualize(query: str):
    chain = chain_workflow(openai_api_key=os.environ.get("OPENAI_API_KEY"))
    result = chain({"question": query})
    response = result['answer']
    print(response)

    return response
