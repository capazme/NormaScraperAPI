import connexion
import sys_op
import text_op
import re
from flask import make_response, jsonify

# Creazione dell'app Connexion
app = connexion.App(__name__, specification_dir='./')
app.add_api('spec.yaml')


    
    
# Implementazione del controllore
def extractLegislation(body):
    act_type = body.get('act_type', '')
    date = body.get('date', '')
    act_number = body.get('act_number', '')
    comma = body.get('comma', '')
    article = body.get('article', '')
    version = body.get('version', 'vigente')
    version_date = body.get('version_date', '')
    timeout = body.get('timeout', 10)

    try:
        print(body)
        results, urn = sys_op.get_urn_and_extract_data(act_type=act_type, date=date, act_number=act_number, comma=comma, article=article, version=version, version_date=version_date, timeout=timeout)
        print(urn)
        if not results:
            raise ValueError("Errore durante l'estrazione dei dati")
        
        out = text_op.parse_out(results=results)

        response = make_response(jsonify(out))
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

if __name__ == '__main__':
    app.run()
