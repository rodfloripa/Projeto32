import os
import sys
import torch
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer

# --- Otimização de CPU (Crítico para AWS Serverless) ---
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

app = Flask(__name__)

print("### [Vector] Iniciando Vector Service...", file=sys.stderr)

try:
    # Usando o modelo padrão do RAG (leve e eficiente: ~80MB)
    # Se ele não estiver na pasta local, ele baixará no primeiro boot
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    print("### [Vector] Modelo de Embeddings carregado com sucesso!", file=sys.stderr)
except Exception as e:
    print(f"### [Vector] ERRO CRÍTICO no carregamento: {e}", file=sys.stderr)
    sys.exit(1)

@app.route('/retrieve', methods=['POST'])
def retrieve():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # O modelo transforma o texto em um vetor (embedding)
        # Em um RAG real, você usaria este vetor para buscar no FAISS/Pinecone
        # Aqui, mantemos a lógica de retorno de contexto do seu projeto
        contexto_recuperado = "A capital do Brasil é Brasília. Foi fundada em 1960."
        
        return jsonify({"context": contexto_recuperado})
    except Exception as e:
        print(f"### [Vector] Erro na requisição: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return "ok", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
