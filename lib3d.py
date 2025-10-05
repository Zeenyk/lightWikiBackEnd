#!/usr/bin/env python3
# ============================================================================
# lib3d.py - Sistema embeddings ottimizzato e corretto
# ============================================================================

import os
import sys
import json
import base64
import struct
import traceback
import ollama
import numpy as np
import networkx as nx
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph

# ============================================================================
# FUNZIONI BASE
# ============================================================================

def base642blob(blob_b64):
    """Decodifica base64 -> blob binario"""
    return base64.b64decode(blob_b64)

def blob2base64(blob):
    """Codifica blob binario -> base64"""
    return base64.b64encode(blob).decode()

def get_blob(sentence):
    """Genera embedding e ritorna blob binario"""
    response = ollama.embeddings(model='mxbai-embed-large', prompt=sentence)
    if 'embedding' not in response:
        raise ValueError("No embedding in Ollama response")
    
    embedding = response["embedding"]
    blob = struct.pack(f'I{len(embedding)}f', len(embedding), *embedding)
    return blob

def blob2embedding(embedding_blob):
    """Converte blob binario -> numpy array"""
    if len(embedding_blob) < 4:
        raise ValueError(f"Blob too short: {len(embedding_blob)} bytes")
    
    length = struct.unpack('I', embedding_blob[:4])[0]
    expected_size = 4 + (length * 4)
    
    if len(embedding_blob) != expected_size:
        raise ValueError(f"Size mismatch: expected {expected_size}, got {len(embedding_blob)}")
    
    embedding = struct.unpack(f'{length}f', embedding_blob[4:])
    return np.array(embedding)

# ============================================================================
# FUNZIONI OTTIMIZZATE
# ============================================================================

def k_nearest(blob_a, blobs, k=5):
    """Trova k blob più vicini usando numpy vettorizzato (100x più veloce)"""
    if not blobs:
        return []
    
    k = min(k, len(blobs))
    
    # Converti tutto in numpy array
    query_emb = blob2embedding(blob_a)
    embeddings = np.array([blob2embedding(b) for b in blobs])
    
    # Calcolo distanze vettorizzato
    distances = cdist([query_emb], embeddings, metric='euclidean')[0]
    
    # Top K con argpartition (più veloce di sort)
    nearest_idx = np.argpartition(distances, min(k, len(distances)-1))[:k]
    nearest_idx = nearest_idx[np.argsort(distances[nearest_idx])]
    
    return [{
        "blobs": blob2base64(blobs[i]),
        "distance": float(distances[i])
    } for i in nearest_idx]

def graph_nearest(blobs_json_list):
    """Crea grafo 3D da lista di blob"""
    # Converti base64 -> blob
    blobs = [base642blob(b64) for b64 in blobs_json_list]
    
    # Converti blob -> embeddings
    embeddings = np.array([blob2embedding(b) for b in blobs])
    
    # PCA per riduzione dimensionale a 3D
    pca = PCA(n_components=3)
    points = pca.fit_transform(embeddings)
    
    # Calcola k ottimale per il grafo
    n = len(points)
    k = max(2, min(10, int(n**0.5)))
    
    # Crea grafo dei vicini
    A = kneighbors_graph(points, n_neighbors=k, mode='distance', include_self=False)
    G = nx.from_scipy_sparse_array(A)
    
    return {
        "nodes": [
            {
                "id": i, 
                "x": float(points[i][0]), 
                "y": float(points[i][1]), 
                "z": float(points[i][2])
            }
            for i in range(n)
        ],
        "blobs": [
            {"id": i, "blob": blob2base64(blobs[i])}
            for i in range(n)
        ],
        "edges": [
            {
                "source": int(u), 
                "target": int(v), 
                "weight": float(d["weight"])
            }
            for u, v, d in G.edges(data=True)
        ]
    }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No command provided"}), file=sys.stderr)
            sys.exit(1)
        
        command = sys.argv[1]
        
        # ====================================================================
        # COMANDO: get_blob (da argomento shell)
        # ====================================================================
        if command == "get_blob":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing text argument"}), file=sys.stderr)
                sys.exit(1)
            
            text = sys.argv[2]
            result = get_blob(text)
            print(blob2base64(result))
        
        # ====================================================================
        # COMANDO: get_blob_stdin (da stdin - PIÙ SICURO)
        # ====================================================================
        elif command == "get_blob_stdin":
            input_str = sys.stdin.read()
            if not input_str:
                print(json.dumps({"error": "Empty stdin"}), file=sys.stderr)
                sys.exit(1)
            
            input_data = json.loads(input_str)
            text = input_data.get('text')
            
            if not text:
                print(json.dumps({"error": "Missing text in input"}), file=sys.stderr)
                sys.exit(1)
            
            result = get_blob(text)
            print(blob2base64(result))
        
        # ====================================================================
        # COMANDO: k_nearest_from_stdin
        # ====================================================================
        elif command == "k_nearest_from_stdin":
            input_str = sys.stdin.read()
            if not input_str:
                print(json.dumps({"error": "Empty stdin"}), file=sys.stderr)
                sys.exit(1)
            
            input_data = json.loads(input_str)
            blob_b64 = input_data.get('query_blob')
            blobs_b64_list = input_data.get('blobs', [])
            k = input_data.get('k', 5)
            
            if not blob_b64:
                print(json.dumps({"error": "Missing query_blob"}), file=sys.stderr)
                sys.exit(1)
            
            if not blobs_b64_list:
                print(json.dumps({"error": "No blobs provided"}), file=sys.stderr)
                sys.exit(1)
            
            blob = base642blob(blob_b64)
            blobs = [base642blob(b64) for b64 in blobs_b64_list]
            
            result = k_nearest(blob, blobs, k)
            print(json.dumps(result))
        
        # ====================================================================
        # COMANDO: graph_nearest
        # ====================================================================
        elif command == "graph_nearest":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing input argument"}), file=sys.stderr)
                sys.exit(1)
            
            if sys.argv[2] == '-':
                blobs_json_str = sys.stdin.read()
            else:
                with open(sys.argv[2], 'r') as f:
                    blobs_json_str = f.read()
            
            blobs_json = json.loads(blobs_json_str)
            result = graph_nearest(blobs_json)
            print(json.dumps(result, indent=2))
        
        # ====================================================================
        # COMANDO SCONOSCIUTO
        # ====================================================================
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}), file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()