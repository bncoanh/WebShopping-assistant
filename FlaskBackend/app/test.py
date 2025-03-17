import numpy as np, faiss, time, string, joblib
from sklearn.preprocessing import MinMaxScaler
from pprint import pprint
from sentence_transformers import SentenceTransformer
from mysql.connector import connect

# SEARCH PRODUCT BY VECTOR
def search_products_by_vector(vector, indexFile: str, k: int):
    index_search = faiss.read_index(f'indices/{indexFile}')
    res = []

    D, I = index_search.search(vector, k)

    db = connect(
        host="localhost",
        user='root',
        password='12345',
        database='ShoppingAssistant'
    )
    db_cursor = db.cursor(dictionary=True)

    for i in I[0]:
        db_cursor.execute('SELECT productId, origin, imgURL, name, link, quantitySold, price, reviewCount, rating, sellerName, brandName FROM Product WHERE productId = %s', (int(i),))
        data = db_cursor.fetchone()
        res.append(data)

    db_cursor.close()
    db.close()
    return res

def search_products_by_query(query):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query_vector = model.encode(query)
    query_vector = query_vector.astype(np.float32).reshape(1, -1)

    res = search_products_by_vector(query_vector, 'search.index', 10)
    return res

def recommend_products_by_history(accountId):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    vectorizer = joblib.load('indices/vectorizer.joblib')
    svd = joblib.load('indices/svd.joblib')
    scaler = MinMaxScaler()
    db = connect(
        host="localhost",
        user='root',
        password='12345',
        database='ShoppingAssistant'
    )
    db_cursor = db.cursor(dictionary=True)

    db_cursor.execute(
        'SELECT productId FROM ProductHistory WHERE accountId = %s',
        (accountId,)
    )
    product_ids = db_cursor.fetchall()
    product_ids = [p['productId'] for p in product_ids] 
    products = []

    for id in product_ids:
        db_cursor.execute(
            'SELECT productId, origin, name, quantitySold, reviewCount, rating, sellerName, brandName FROM Product WHERE productId = %s',
            (id,)
        )
        products.append(db_cursor.fetchone())
    ids = []
    names_categories = []
    metadata = []
    numerical_fields = []
    for p in products:
        ids.append(p['productId'])
        name_category_elem = p['name'].strip() if p['name'].strip().endswith(string.punctuation) else p['name'].strip() + '.'
        db_cursor.execute(
            '''
            SELECT c.name AS name
            FROM Product_Category AS pc
            JOIN Category AS c ON c.categoryId = pc.categoryId AND c.origin = pc.categoryOrigin
            WHERE pc.productId = %s AND c.origin = %s
            ''',
            (p['productId'], p['origin'])
        )
        categories = db_cursor.fetchall()
        for ci in range(len(categories)):
            if ci == 0:
                name_category_elem += (' ' + categories[ci]['name'])
            else:
                name_category_elem += (', ' + categories[ci]['name'])
            if ci == len(categories) - 1:
                name_category_elem += '.'
        names_categories.append(name_category_elem)      
        metadata.append(str.lower(p['origin']) + ' ' + str.lower(p['sellerName'].replace(' ', '')) + ' ' + str.lower(p['brandName'].replace(' ', '')))
        numerical_fields.append([p['quantitySold'], p['reviewCount'], p['rating']])

    ids = np.array(ids).astype(np.int64)
    names_categories = model.encode(names_categories)
    names_categories = names_categories.astype(np.float32)
    metadata = vectorizer.transform(metadata)
    metadata = svd.transform(metadata)
    metadata = np.array(metadata).astype(np.float32)
    numerical_fields = scaler.fit_transform(numerical_fields)
    numerical_fields = np.array(numerical_fields).astype(np.float32)

    combined_vectors = np.hstack((names_categories, metadata, numerical_fields))
    avg_vector = np.mean(combined_vectors, axis=0).reshape(1, -1)
    res = search_products_by_vector(avg_vector, 'recommendation.index', 40)

    db_cursor.close()
    db.close()
    return res
