import os
import sys
import torch
from flask import Flask, request, jsonify
from transformers import T5Tokenizer, T5ForConditionalGeneration

# --- Otimização de Recursos ---
# Força o uso de apenas 1 thread para evitar que o container trave a CPU
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

app = Flask(__name__)

# Usamos o nome do modelo para o Hugging Face baixar automaticamente no primeiro boot
# O 'flan-t5-small' ocupa apenas ~300MB de RAM.
MODEL_NAME = "google/flan-t5-small"

print(f"### [LLM] Iniciando carregamento do modelo {MODEL_NAME}...", file=sys.stderr)

try:
    # Carrega o Tokenizador e o Modelo
    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    print("### [LLM] Modelo carregado com sucesso na porta 5002!", file=sys.stderr)
except Exception as e:
    print(f"### [LLM] ERRO CRÍTICO no carregamento: {e}", file=sys.stderr)
    sys.exit(1)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', '')

        # Formata o prompt seguindo o padrão T5
        input_text = f"answer the question using the context: context: {context} question: {query}"
        
        # Tokenização (converte texto para números)
        inputs = tokenizer(input_text, return_tensors="pt")

        # Geração da resposta
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=100,
                do_sample=True,
                top_p=0.9
            )

        # Decodificação (converte números de volta para texto)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"### [LLM] Resposta gerada para a query: {query[:30]}...", file=sys.stderr)
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"### [LLM] Erro durante a geração: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return "ok", 200

if __name__ == '__main__':
    # O microserviço roda interno na porta 5002
    app.run(host='0.0.0.0', port=5002)
