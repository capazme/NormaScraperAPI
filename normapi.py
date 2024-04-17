from autourn import get_urn_and_extract_data, create_driver
from flask import jsonify, make_response

def norma_scraper(body):
    act_type = body['act_type']
    date = body['date']
    act_number = body['act_number']
    comma = body.get('comma')
    article = body.get('article')
    extension = body.get('extension')
    version = body.get('version')
    version_date = body.get('version_date')
    timeout = body.get('timeout', 10)
    
    
    try:
        driver = create_driver() 
        data = get_urn_and_extract_data(driver, act_type, date, act_number, article, extension, comma, version, version_date, timeout)
        
        if data is None:
            raise Exception("Errore nella generazione dell'URN o nell'esportazione dei dati.")
        
        content_type = 'application/xml'
        response = make_response(data, 200)
        response.headers['Content-Type'] = content_type
        return response
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

