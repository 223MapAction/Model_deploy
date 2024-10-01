from pgml import OpenSourceAI, Model, Collection, Pipeline
from ..llm.pgml_llm_preprocessing import chat_flow

client = OpenSourceAI()
conninfo = "postgres://root:postgresml@localhost:5433/postgresml"

system_message = "You're an AI assistant"

history = [{"role": "system", "content": ""}]

# collection = Collection("MapActionManifesto", conninfo)
# pipeline = Pipeline("Main_Pipeline")


def build_history_with_context(context):
    history[0]["content"] = system_message.replace("{context}", context)
    return history


async def chat_bot(query: str) -> str:

    collection, pipeline = await chat_flow()

    history.append({"role": "user", "content": query})

    context = await (
        collection.query()
        .vector_recall(query, pipeline)
        .limit(1)
        .fetch_all()
    )

    new_history = build_history_with_context(context[0][1])
    model_output = client.chat_completions_create(
        "teknium/OpenHermes-2.5-Mistral-7B", new_history, temperature=0.85
    )

    history.append(
        {
            "role": "assistant",
            "content": model_output["choices"][0]["message"]["content"],
        }
    )

    return model_output["choices"][0]["message"]["content"]
