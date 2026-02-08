import os
import sys
import time
import requests
import flask

app = flask.Flask(__name__)

def call_with_retry(url, payload, name, retries=15):
    """
    Tenta conectar nos microserviços internos.
    Usa timeouts curtos para não deixar o Gunicorn matar o processo por inatividade.
    """
    for i in range(retries):
        try:
            # Timeout de 3s é o 'ponto doce': tempo para o serviço responder,
            # mas rápido o suficiente para o loop girar e mostrar que o app está vivo.
            r = requests.post(url, json=payload, timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            # Imprime no stderr para aparecer no CloudWatch
            print(f"[Orquestrador] {name} ainda não respondeu (tentativa {i+1}/{retries})", file=sys.stderr)
            # Sleep curto para manter o processo "ativo" aos olhos do Gunicorn
            time.sleep(2)
    return None

@app.route('/invocations', methods=['POST'])
def invocations():
    """
    Ponto de entrada principal do SageMaker.
    """
    try:
        data = flask.request.get_json(force=True)
        query = data.get('query', '')
        
        if not query:
            return flask.jsonify({"error": "Query vazia"}), 400

        # ETAPA 1: Busca de Contexto no Vector Service (Porta 5001)
        print(f"### [Orquestrador] Chamando Vector Service para: {query}", file=sys.stderr)
        v_res = call_with_retry("http://127.0.0.1:5001/retrieve", {"query": query}, "VectorService")
        
        if not v_res:
            return flask.jsonify({"error": "Vector Service não ficou pronto a tempo"}), 503
        
        context = v_res.get('context', '')

        # ETAPA 2: Geração de Resposta no LLM Service (Porta 5002)
        print(f"### [Orquestrador] Chamando LLM Service com contexto recuperado", file=sys.stderr)
        l_res = call_with_retry("http://127.0.0.1:5002/generate", {"query": query, "context": context}, "LLMService")
        
        if not l_res:
            return flask.jsonify({"error": "LLM Service não ficou pronto a tempo"}), 503

        # Retorno final para o usuário
        return flask.jsonify({
            "pergunta": query,
            "resposta": l_res.get('answer'),
            "contexto_usado": context,
            "status": "sucesso"
        })

    except Exception as e:
        print(f"### [ERRO NO ORQUESTRADOR]: {str(e)}", file=sys.stderr)
        return flask.jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    """
    O SageMaker usa isso para saber se o container está vivo.
    Sempre responde 200 rápido.
    """
    return flask.Response(response="\n", status=200, mimetype='application/json')

if __name__ == '__main__':
    # Em produção (SageMaker), o Gunicorn ignora esta parte e chama o 'app' diretamente.
    app.run(host='0.0.0.0', port=8080)
