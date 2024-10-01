import os
import torch
from transformers import (
  AutoTokenizer, 
  AutoModelForCausalLM, 
  BitsAndBytesConfig,
  pipeline
)

from transformers import BitsAndBytesConfig

from langchain.text_splitter import CharacterTextSplitter
from langchain.document_transformers import Html2TextTransformer
from langchain.document_loaders import AsyncChromiumLoader

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.llms import HuggingFacePipeline
from langchain.chains import LLMChain

import nest_asyncio



model_name='mistralai/Mistral-7B-Instruct-v0.1'

model_config = transformers.AutoConfig.from_pretrained(
    model_name,
)

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"



