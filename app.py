import connexion

# Crea l'applicazione Connexion
app = connexion.App(__name__, specification_dir='./')

# Legge la specifica OpenAPI e la configura con l'API
app.add_api('spec.yaml')

if __name__ == '__main__':
    app.run()