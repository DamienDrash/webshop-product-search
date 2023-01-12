import json
import pyexasol
import elasticsearch
from elasticsearch_dsl import connections
import redis
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


class ProductSearch:
    def __init__(self):
        # Verbindung mit der Exasol-Datenbank herstellen
        self.conn = pyexasol.connect(dsn=f"{config['DWH']['Host']}:{config['DWH']['Port']}", user=config['DWH']['User'],
                                     password=config['DWH']['Password'])

        # Verbindung mit Elasticsearch herstellen
        self.es = elasticsearch.Elasticsearch(hosts=[
            f"{config['ELASTICSERACH']['Schema']}://{config['ELASTICSERACH']['Host']}:{config['ELASTICSERACH']['Port']}"])
        # self.es = elasticsearch.Elasticsearch(URL, http_auth=('elastic', ELASTIC_PASSWORD), verify_certs=False)
        connections.add_connection('default', self.es)

        # Verbindung mit Redis-Cache herstellen
        self.cache = redis.Redis(host=str(config['REDIS']['Host']), port=int(config['REDIS']['Port']),
                                 db=int(config['REDIS']['DB']))

        self.query = """
        SELECT
            p.PRODUCT_ID,
            p.P_NAME,
            p.P_PRICE,
            p.P_SKU,
            p.P_ORIGINAL_MATS_ID,
            NULL as P_CATEGORY_NAME,
            NULL as P_BRAND_NAME,
            p.P_GENDER,
            p.P_EAN
        FROM AAA_01_DWH.PRODUCT p
        WHERE P_BRAND_NAME = 'Satisfyer';
        """

        self.update_query = self.query + " WHERE P_CREATED_AT > NOW() - INTERVAL '1 HOUR';"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Verbindungen beim Verlassen des Kontextmanagers schließen
        self.conn.close()
        self.es.transport.close()
        self.cache.close()

    def init_index(self):
        # Check if the index exists
        if self.es.indices.exists(index='products'):
            self.es.indices.delete(index='products')

        # Create the index if it does not exist
        self.es.indices.create(index='products')

    def load_products(self):
        # Ergebnisse der Abfrage abrufen
        results = self.conn.execute(self.query).fetchall()

        mapping = {
            'properties': {
                'id': {'type': 'long'},
                'name': {'type': 'text'},
                'price': {'type': 'text'},
                'sku': {'type': 'text'},
                'mats_id': {'type': 'text'},
                'category': {'type': 'text'},
                'brand': {'type': 'text'},
                'gender': {'type': 'text'},
                'ean': {'type': 'text'},
                'name_suggest': {
                    'type': 'completion',
                    'analyzer': 'simple',
                    'preserve_separators': True,
                    'preserve_position_increments': True,
                    'max_input_length': 50
                }
            }
        }

        self.es.indices.put_mapping(
            index='products',
            body=mapping
        )

        # Produktdaten in Elasticsearch-Index laden
        for row in results:
            doc = {
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'sku': row[3],
                'mats_id': row[4],
                'category': row[5],
                'brand': row[6],
                'gender': row[7],
                'ean': row[8],
                'name_suggest': {
                    'input': row[1],
                    'weight': 10,
                }
            }
            print(doc)
            self.es.index(index='products', id=doc['id'], body=doc)

            # Ergebnisse im Cache aktualisieren
            cache_key = 'search-' + doc['name']
            json_string = json.dumps(doc)
            self.cache.set(cache_key, json_string)

    def update_mapping(self):
        self.es.indices.put_mapping(
            index='products',
            body={
                'properties': {
                    'name_suggest': {
                        "type": "completion",
                        "analyzer": "simple",
                        "preserve_separators": True,
                        "preserve_position_increments": True,
                        "max_input_length": 50
                    }
                }
            }
        )

    def update_products(self):
        # Geänderte Produktdaten abrufen
        updated_products = self.conn.execute(self.update_query).fetchall()

        # Änderungen in Elasticsearch und Redis aktualisieren
        for row in updated_products:
            doc = {
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'sku': row[3],
                'mats_id': row[4],
                'category': row[5],
                'brand': row[6],
                'gender': row[7],
                'ean': row[8],
                'name_suggest': {
                    'input': row[1],
                    'weight': 10,
                    'type': 'completion'
                }
            }
            self.es.index(index='products', id=doc['id'], body=doc)

            # Ergebnisse im Cache aktualisieren
            cache_key = 'search-' + doc['name']
        try:
            self.cache.set(cache_key, doc)
        except redis.exceptions.DataError:
            self.cache.set(cache_key, json.dumps(doc))

    def search(self, query):
        # Abfrage im Cache suchen
        cache_key = 'search-' + query
        cached_results = self.cache.get(cache_key)
        if cached_results:
            return cached_results

        # Elasticsearch-Abfrage durchführen
        results = self.es.search(index='products', q=query)

        # Ergebnisse in geeignetes Format umwandeln
        formatted_results = []
        for hit in results['hits']['hits']:
            doc = hit['_source']
            formatted_results.append({
                'id': doc['id'],
                'name': doc['name'],
                'price': doc['price'],
                'category': doc['category'],
                'brand': doc['brand'],
                'ean': doc['ean'],
            })

        # Ergebnisse cachen und zurückgeben
        try:
            self.cache.set(cache_key, formatted_results)
        except redis.exceptions.DataError:
            self.cache.set(cache_key, json.dumps(formatted_results))
        return formatted_results

    def get_suggestions(self, query):
        if not query:
            return []

        res = self.es.search(index='products', body={
            'suggest': {
                'field-suggest': {
                    'prefix': query,
                    'completion': {
                        'field': 'name_suggest',
                        'fuzzy': {'fuzziness': 2},
                        'size': 10
                    }
                }
            }
        })

        print('Got %d Hits:' % res['hits']['total']['value'])
        for hit in res['hits']['hits']:
            print(hit['_source'])
        return res['suggest']['field-suggest'][0]['options']


if __name__ == '__main__':
    with ProductSearch() as search:
        # search.init_index()
        # search.load_products()
        # search.update_mapping()
        print(search.get_suggestions('satis'))
