import flask
from flask_cors import CORS
import src.product_search as product_search

app = flask.Flask(__name__)
search = product_search.ProductSearch()

CORS(app)


@app.route('/search')
def search_products():
    # Suchbegriff aus der Anfrage abrufen
    query = flask.request.args.get('query')

    # Suchabfrage durchführen und Ergebnisse abrufen
    results = search.search(query)

    # Ergebnisse als JSON zurückgeben
    return results


@app.route('/suggestions')
def products_suggestions():
    # Suchbegriff aus der Anfrage abrufen
    query = flask.request.args.get('query')

    # Suchabfrage durchführen und Ergebnisse abrufen
    results = search.get_suggestions(query)

    # Ergebnisse als JSON zurückgeben
    return results


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/update')
def update_products():
    # Produktdaten aktualisieren
    search.update_products()

    # Bestätigung zurückgeben
    return 'Update successful!'
