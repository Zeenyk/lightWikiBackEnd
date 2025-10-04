import os
import ollama
import struct
from openai import OpenAI
from dotenv import load_dotenv
from scipy.spatial.distance import euclidean

# * import openai key saved on .env file
load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"), base_url="https://api.deepseek.com")

# * function to return a "blobbed" embedding of the sentence
def get_blob(sentence):
    embedding = ollama.embeddings(model='mxbai-embed-large', prompt=sentence)["embedding"]
    blob = struct.pack(f'I{len(embedding)}f', len(embedding), *embedding)

    return blob

# * function to convert blob to embedding
def blob2embedding(embedding_blob):
    length = struct.unpack('I', embedding_blob[:4])[0]
    embedding = list(struct.unpack(f'{length}f', embedding_blob[4:]))

    return embedding

# * distance between 2 blobs
def blob_distance(blob_a, blob_b):
    embedding_a = blob2embedding(blob_a)
    embedding_b = blob2embedding(blob_b)

    return euclidean(embedding_a, embedding_b) 

