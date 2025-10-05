import os
import ollama
import struct
import base64
import json
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from scipy.spatial.distance import euclidean
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph

# * import openai key saved on .env file
load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"), base_url="https://api.deepseek.com")


def json2list(json):
    blobs = [base642blob(b64) for b64 in json["blobs"]]
    return blobs


def json2points(blobs_json):
    blobs = json2list(blobs_json)
    embeddings = [blob2embedding(b) for b in blobs]

    pca = PCA(n_components=3)
    points_3d = pca.fit_transform(embeddings)
    points_3d_list = points_3d.tolist()

    return points_3d_list

def base642blob(blob_b64):
    return base64.b64decode(blob_b64)

def blob2base64(blob):
    return base64.b64encode(blob).decode()

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

def k_nearest(blob_a, blobs_json, k=5):
    blobs = json2list(blobs_json) 

    distances = [(blob, blob_distance(blob_a, blob)) for blob in blobs]
    distances.sort(key=lambda x: x[1])

    embeddings = [(blob, dist) for blob, dist in distances[:k]]
    embeddings_json = [{
        "blobs": blob,  # lista di float
        "distance": float(dist)   # converti a float per sicurezza
    }for blob, dist in embeddings]

    return embeddings_json


def calculate_optimal_zone_range(n_points):
    base = max(3, int(np.log(n_points) * 2))
    return max(2, int(base * 0.6)), min(n_points // 5, int(base * 1.4))

def find_optimal_neighbors_fast(points, target_zones_range=(5, 20), max_neighbors=10):
    n_points = len(points)
    low, high = 2, min(max_neighbors, n_points - 1)
    best_k, best_count = 3, 0
    initial_k = max(2, int(n_points**0.5))

    def zone_count(k):
        G = nx.from_scipy_sparse_array(
            kneighbors_graph(points, n_neighbors=k, mode='connectivity', include_self=False)
        )
        return len(list(nx.connected_components(G)))

    count = zone_count(initial_k)
    if target_zones_range[0] <= count <= target_zones_range[1]:
        return initial_k, count

    for _ in range(5):
        mid = (low + high) // 2
        count = zone_count(mid)
        if target_zones_range[0] <= count <= target_zones_range[1]:
            return mid, count
        if count < target_zones_range[0]:
            high = mid - 1
        else:
            low = mid + 1
        if abs(count - sum(target_zones_range)/2) < abs(best_count - sum(target_zones_range)/2):
            best_k, best_count = mid, count

    return best_k, best_count




def graph_nearest(blobs_json):
    points = json2points(blobs_json)
    blobs = json2list(blobs_json)

    min_zones, max_zones = calculate_optimal_zone_range(len(points))
    optimal_k, zone_count = find_optimal_neighbors_fast(points, target_zones_range=(min_zones, max_zones))

    A = kneighbors_graph(points, n_neighbors=optimal_k, mode='distance', include_self=False)
    G = nx.from_scipy_sparse_array(A)

    graph_json = {
        "nodes": [
            {"id": i, "x": float(points[i][0]), "y": float(points[i][1]), "z": float(points[i][2])} 
            for i in range(len(points))],
        "blobs": [{"id": i, "blob": blob2base64(blobs[i])} for i in range(len(blobs))],
        "edges": [{"source": int(u), "target": int(v), "weight": float(d["weight"])}
            for u, v, d in G.edges(data=True)]
    }

    return graph_json


with open("embeddings_blob.json", "r", encoding="utf-8") as f:
    data = json.load(f)

graph = graph_nearest(data)
with open("graph3d.json", "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=2)
print("Saved 3D graph JSON to graph3d.json")
