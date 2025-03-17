from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import sqlite3, json, faiss, numpy as np, time, tracemalloc, joblib
import string
from mysql.connector import Error
from app.auth import admin_login_required
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import MinMaxScaler
from .models import *
from tiki import TikiScraper
from lazada import LazadaScraper, preprocess_data

bp = Blueprint('data', __name__, url_prefix='/api/data')

batch_size = 5000

@bp.route('/load_tiki', methods=('POST',))
@admin_login_required
def load_tiki():
    """
    Load data from Tiki into the database.

    This function will process the Tiki data stored in 'tiki/tiki.db',
    delete existing records related to Tiki in the `Category`, `Product`,
    `Product_Category`, and `ProductHistory` tables, and then insert new records
    from the file into the database. The records in `ProductHistory` will also be
    updated accordingly.

    :API: POST /api/data/load_tiki

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Load Tiki data successful!"}, 201
    - Failed to take Tiki data: {"success": False, "message": "Cannot take the Tiki data."}, 404
    - Failed to put data into database: {"success": False, "message": "Cannot put the Tiki data into the database."}, 409
    """
    if request.method == 'POST':
        origin = 'tiki'
        tiki_conn = sqlite3.connect('tiki/tiki.db')
        try:
            tiki_cursor = tiki_conn.cursor()

            product_histories = ProductHistory.ProductHistory.get_product_histories_by_origin(origin)

            ProductHistory.ProductHistory.delete_by_origin(origin)

            Product_Category.Product_Category.delete_by_origin(origin)

            Product.Product.delete_by_origin(origin)

            Category.Category.delete_by_origin(origin)

            tiki_cursor.execute('SELECT id, name, thumbnail_url, is_leaf FROM category')
            while True:
                rows = tiki_cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    Category.Category(categoryId=row[0], origin=origin, name=row[1], imgURL=row[2], isLeaf=row[3]).add()
            tiki_cursor.execute('SELECT id, parent_id FROM category')
            while True:
                rows = tiki_cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    Category.Category.update_parentId_parentOrigin(categoryId=row[0], origin=origin, parentId=row[1])
            tiki_cursor.execute('SELECT id, thumbnail_url, name, link, quantity_sold, price, review_count, rating_average, seller_name, brand_name FROM product')
            while True:
                rows = tiki_cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    Product.Product(productId=row[0], origin=origin, imgURL=row[1], name=row[2], link=row[3], quantitySold=row[4], price=row[5], reviewCount=row[6], rating=row[7], sellerName=row[8], brandName=row[9]).add()
            category_ids = [i.categoryId for i in Category.Category.get_categories_by_origin(origin)]
            tiki_cursor.execute('SELECT id, category_path, direct_category FROM product')
            while True:
                rows = tiki_cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    path = row[1].strip('[]').split(', ')
                    path = [i.strip("'") for i in path]
                    int_path = [int(i) for i in path]
                    if row[2] not in int_path:
                        int_path.append(row[2])
                    for i in int_path:
                        if i in category_ids:
                            Product_Category.Product_Category(productId=row[0], categoryId=i, productOrigin=origin, categoryOrigin=origin).add()
            product_ids = [i.productId for i in Product.Product.get_products_by_origin(origin=origin)]
            for history in product_histories:
                if history.productId in product_ids:
                    ProductHistory.ProductHistory(accountId=history.accountId, productId=history.productId, origin=origin, createAt=history.createAt).add()
        except sqlite3.Error as e:
            print(e)
            return {"success": False, "message": "Cannot take the Tiki data."}, 404
        except Error as e:
            print(e)
            return {"success": False, "message": "Cannot put the Tiki data into the database."}, 409
        finally:
            tiki_cursor.close()
            tiki_conn.close()

        return {"success": True, "message": "Load Tiki data successful!"}, 201

@bp.route('/load_lazada', methods=('POST',))
@admin_login_required
def load_lazada():
    """
    Load data from Lazada into the database.

    This function will process the Lazada data stored in 'lazada/preprocess_data.json',
    delete existing records related to Lazada in the `Category`, `Product`, 
    `Product_Category`, and `ProductHistory` tables, and then insert new records 
    from the file into the database. The records in `ProductHistory` will also be updated accordingly.

    :API: POST /api/data/load_lazada

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Load Lazada data successful!"}, 201
    - Failed to take Lazada data: {"success": False, "message": "Cannot take the Lazada data."}, 404
    - Failed to put data into database: {"success": False, "message": "Cannot put the Lazada data into the database."}, 409
    """
    if request.method == 'POST':
        origin = 'lazada'
        try:
            with open('lazada/preprocess_data.json', encoding='utf-8') as file:
                jsobj = json.load(file)
        except Exception as e:
            print(e)
            return {"success": False, "message": "Cannot take the Lazada data."}, 404
        try:
            product_histories = ProductHistory.ProductHistory.get_product_histories_by_origin(origin)
            ProductHistory.ProductHistory.delete_by_origin(origin)
            Product_Category.Product_Category.delete_by_origin(origin)
            Product.Product.delete_by_origin(origin)
            Category.Category.delete_by_origin(origin)

            for product in jsobj:
                if product['name'] != '':
                    try:
                        Product.Product(productId=product["itemId"],origin=origin, imgURL=product["imageUrl"], name=product["name"], link=f'https:{product["itemUrl"]}', quantitySold=product["itemSoldCntShow"], price=product["priceShow"], reviewCount=product["review"], rating=product["ratingScore"], sellerName=product["sellerName"], brandName=product["brandName"]).add()
                    except Error:
                        print(f'Sản phẩm {product["itemId"]} đã được thêm trước đó.')
                        continue
                    try:
                        Category.Category(categoryId=product["categorieId"], origin=origin, name=product["category_name"], isLeaf=False).add()
                    except Error:
                        print(f'Danh mục {product["categorieId"]} đã được thêm trước đó.')
                    try:
                        Category.Category(categoryId=product["tabId"], origin=origin, name=product["tab_name"], isLeaf=True, parentId=product["categorieId"], parentOrigin=origin).add()
                    except Error:
                        print(f'Danh mục {product["tabId"]} đã được thêm trước đó.')
                    Product_Category.Product_Category(productId=product["itemId"], categoryId=product["categorieId"], productOrigin=origin, categoryOrigin=origin).add()
                    Product_Category.Product_Category(productId=product["itemId"], categoryId=product["tabId"], productOrigin=origin, categoryOrigin=origin)
            product_ids = [i.productId for i in Product.Product.get_products_by_origin(origin)]
            for history in product_histories:
                if history.productId in product_ids:
                    ProductHistory.ProductHistory(accountId=history.accountId, productId=history.productId, origin=origin, createAt=history.createAt)
        except Error as e:
            print(e)
            return {"success": False, "message": "Cannot put the Lazada data into the database."}, 409

        return {"success": True, "message": "Load Lazada data successful!"}, 201
    
@bp.route('/create_index', methods=('POST',))
@admin_login_required
def create_index():
    """
    Create search and recommendation indices.

    This function will create two indices, one for search and one for recommendation.

    The search index is a flat index with 384 dimensions, each dimension is the
    sentence embedding of the product name.

    The recommendation index is a flat index with 488 dimensions, each dimension is
    the concatenation of the sentence embedding of the product name, the category
    name, the seller name, the brand name, and the numerical fields (quantitySold,
    reviewCount, rating).

    :API: POST /api/data/create_index

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Create index successful!"}, 201
    - Failed to take data from database: {"success": False, "message": "Cannot take data from database."}, 409
    """
    start = time.time()

    model = SentenceTransformer('all-MiniLM-L6-v2')
    vectorizer = CountVectorizer()
    svd = TruncatedSVD(n_components=101)
    scaler = MinMaxScaler()

    search_dim = 384
    search_index = faiss.IndexFlatIP(search_dim)
    search_index = faiss.IndexIDMap(search_index)

    recommendation_dim = 488
    recommendation_index = faiss.IndexFlatIP(recommendation_dim)
    recommendation_index = faiss.IndexIDMap(recommendation_index)

    try:
        products = Product.Product.get_products()

        ids = []
        names = []
        names_categories = []
        metadata = []
        numerical_fields = []
        for p in products:
            ids.append(p.productId)
            names.append(p.name)
            name_category_elem = p.name.strip() if p.name.strip().endswith(string.punctuation) else p.name.strip() + '.'
            categories = Category.Category.get_categories_by_productId_origin(p.productId, p.origin)
            for ci in range(len(categories)):
                if ci == 0:
                    name_category_elem += (' ' + categories[ci].name)
                else:
                    name_category_elem += (', ' + categories[ci].name)
                if ci == len(categories) - 1:
                    name_category_elem += '.'
            names_categories.append(name_category_elem)      
            metadata.append(str.lower(p.origin) + ' ' + str.lower(p.sellerName.replace(' ', '')) + ' ' + str.lower(p.brandName.replace(' ', '')))
            numerical_fields.append([p.quantitySold, p.reviewCount, p.rating])

        names = model.encode(names)
        names = names.astype(np.float32)
        ids = np.array(ids).astype(np.int64)
        names_categories = model.encode(names_categories)
        names_categories = names_categories.astype(np.float32)
        metadata = vectorizer.fit_transform(metadata)
        metadata = svd.fit_transform(metadata)
        metadata = np.array(metadata).astype(np.float32)
        numerical_fields = scaler.fit_transform(numerical_fields)
        numerical_fields = np.array(numerical_fields).astype(np.float32)

        faiss.normalize_L2(names)
        search_index.add_with_ids(names, ids)
        
        faiss.write_index(search_index, 'indices/search.index')
        del names

        combined_vectors = np.hstack((names_categories, metadata, numerical_fields))
        faiss.normalize_L2(combined_vectors)
        recommendation_index.add_with_ids(combined_vectors, ids)

        faiss.write_index(recommendation_index, 'indices/recommendation.index')

        joblib.dump(vectorizer, 'indices/vectorizer.joblib')
        joblib.dump(svd, 'indices/svd.joblib')

    except Error as e:
        print(e)
        return {"success": False, "message": "Cannot take data from database."}, 409

    end = time.time()
    print(f'Thời gian tạo index: {end - start}')

    return {"success": True, "message": "Create index successful!"}, 201

@bp.route('/crawl_tiki', methods=('POST',))
@admin_login_required
def crawl_tiki():
    """
    Crawl data from Tiki.

    This function will crawl data from Tiki and put it into the sqlite file.

    :API: POST /api/data/crawl_tiki

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Crawl Tiki successful!"}, 201
    - Failed to crawl data: {"success": False, "message": "Crawl Tiki failed!"}, 500
    """
    
    try:
        TikiScraper.main()
    except Exception as e:
        print(e)
        return {"success": False, "message": "Crawl Tiki failed!"}, 500
    return {"success": True, "message": "Crawl Tiki successful!"}, 201

@bp.route('/crawl_lazada', methods=('POST',))
@admin_login_required
def crawl_lazada():
    """
    Crawl data from Lazada.

    This function will crawl data from Lazada and put it into the json file.

    :API: POST /api/data/crawl_lazada

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Crawl Lazada successful!"}, 201
    - Failed to crawl data: {"success": False, "message": "Crawl Lazada failed!"}, 500
    """
    try:
        LazadaScraper.main()
        preprocess_data.main() 
    except Exception as e:
        print(e)
        return {"success": False, "message": "Crawl Lazada failed!"}, 500
    return {"success": True, "message": "Crawl Lazada successful!"}, 201