from sys_op import get_urn_and_extract_data
from flask import jsonify, make_response

def norma_scraper(body):
    act_type = body.get('act_type')
    date = body.get('date')
    act_number = body.get('act_number')
    comma = body.get('comma')
    article = body.get('article')
    extension = body.get('extension')
    version = body.get('version')
    version_date = body.get('version_date')
    timeout = body.get('timeout', 10)
    
    
    try:
        data, url, estremi = get_urn_and_extract_data(act_type, date, act_number, article, extension, comma, version, version_date, timeout)
        print(estremi,url)
        if data is None:
            raise Exception("Errore nella generazione dell'URN o nell'esportazione dei dati.")
        
        content_type = 'application/xml'
        response = make_response(data, 200)
        response.headers['Content-Type'] = content_type
        return response
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

