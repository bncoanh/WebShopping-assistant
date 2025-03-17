from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import faiss, numpy as np, joblib, string
from werkzeug.exceptions import abort
from app.auth import login_required
from mysql.connector import Error
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import MinMaxScaler
from .models import *

bp = Blueprint('product', __name__, url_prefix='/api/product')

def get_categories(origin: str) -> list[dict]:
    """
    Get all categories from database by origin.

    :param origin: Origin of categories, can be "tiki" or "lazada".
    :type origin: str
    :return: List of categories
    :rtype: list[dict]
    :raises: mysql.connector.Error
    """
    res = []
    categories = Category.Category.get_categories_by_origin(origin)

    for c in categories:
        res.append({
            'categoryId': c.categoryId,
            'origin': c.origin,
            'name': c.name,
            'imgURL': c.imgURL,
            'isLeaf': c.isLeaf,
            'children': []
        })

    is_not_leaf_queue = []
    for c in res:
        if c['isLeaf']:
            continue
        else:
            is_not_leaf_queue.append(c)

    while len(is_not_leaf_queue) > 0:
        cur_category = is_not_leaf_queue.pop(0)
        categories = Category.Category.get_categories_by_parentId_origin(cur_category['categoryId'], origin)

        for c in categories:
            cur_category['children'].append({
                'categoryId': c.categoryId,
                'origin': c.origin,
                'name': c.name,
                'imgURL': c.imgURL,
                'isLeaf': c.isLeaf,
                'children': []
            })
            if not c.isLeaf:
                is_not_leaf_queue.append(cur_category['children'][-1])

    return res

@bp.route('/<string:origin>/get_categories')
def get_categories_by_origin(origin: str):
    """
    Get all categories from Tiki.

    :API: GET /api/product/<string:origin>/get_categories

    :param origin: The origin of the category, can be "tiki" or "lazada".

    :return: 1 of the following cases:
    - Successful: {"success": True, "data": categories}, 200
    - No categories found: {"success": False, "message": "No categories found."}, 404
    :dataformat: json with the following structure:
    [
        {
            "categoryId": int,
            "name": string,
            "imgURL": string,
            "isLeaf": bool,
            "children": [
                {
                    "categoryId": int,
                    "name": string,
                    "imgURL": string,
                    "isLeaf": bool,
                    "children": []
                },
                ...
            ]
        },
        ...
    ]
    """
    res = get_categories(origin)
    if len(res) == 0:
        return {"success": False, "message": "No categories found."}, 404
    else:
        return {"success": True, "data": res}, 200

@bp.route('/<string:origin>/category/<int:categoryId>/<int:page>')
def get_products_by_category(origin: str, categoryId: int, page: int):
    """
    Get all products in a category from the given origin.

    :API: GET /api/product/<string:origin>/category/<int:categoryId>/<int:page>

    :param origin: The origin of the category, can be "tiki" or "lazada".
    :param categoryId: The id of the category.
    :param page: The page number of the products to be retrieved.

    The request body should be a JSON object with the following structure:
    {
        "order_by": string,
        "type": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "current_page": int, "max_page": int, "per_page": int, "total_products": int, "data": products}, 200
    - No products found: {"success": False, "message": "No products found."}, 404
    - Invalid page number: {"success": False, "message": "Invalid page number."}, 404
    :dataformat: json with the following structure: a array with 40 products (except for the last page)
    [
        {
            "productId": int,
            "origin": string,
            "imgURL": string,
            "name": string,
            "quantitySold": int,
            "price": float,
            "reviewCount": int,
            "rating": float
        },
        ...
    ]
    """
    if page < 1:
        return {"success": False, "message": "Invalid page number."}, 404
    per_page = 40

    body = request.get_json()
    order_by = body.get('order_by')
    type = body.get('type')
    if order_by == 'normal':
        products = Product.Product.get_products_by_category(origin, categoryId)
    else:
        products = Product.Product.get_products_by_category_order(origin, categoryId, order_by, type)

    if len(products) == 0:
        return {"success": False, "message": "No products found."}, 404
    else:
        start = (page - 1) * per_page
        end = start + per_page
        bonus_page = 0 if len(products) % per_page == 0 else 1
        max_page = len(products) // per_page + bonus_page
        if page > max_page:
            return {"success": False, "message": "Invalid page number."}, 404
        data = []
        for p in products[start:end]:
            data.append(
                {
                    "productId": p.productId,
                    "origin": p.origin,
                    "imgURL": p.imgURL,
                    "name": p.name,
                    "quantitySold": p.quantitySold,
                    "price": p.price,
                    "reviewCount": p.reviewCount,
                    "rating": p.rating
                }
            )
        return {"success": True, "current_page": page, "max_page": max_page, "per_page": per_page, "total_products": len(products), "data": data}, 200

@bp.route('/<string:origin>/product/<int:productId>')
def get_product_by_id(origin: str, productId: int):
    """
    Get a product by its id from the given origin.

    :API: GET /api/product/<string:origin>/product/<int:productId>

    :param origin: The origin of the product, can be "tiki" or "lazada".
    :param productId: The id of the product.

    :return: 1 of the following cases:
    - Successful: {"success": True, "data": product}, 200
    - Product not found: {"success": False, "message": "Product not found."}, 404
    :dataformat: json with the following structure:
    {
        "productId": int,
        "origin": string,
        "imgURL": string,
        "name": string,
        "link": string,
        "quantitySold": int,
        "price": float,
        "reviewCount": int,
        "rating": float,
        "sellerName": string,
        "brandName": string,
        "reviewSummary": string
    }
    """
    product = Product.Product.get_product_by_productId_origin(productId, origin)

    if product is None:
        return {"success": False, "message": "Product not found."}, 404
    else:
        product = {
            "productId": product.productId,
            "origin": product.origin,
            "imgURL": product.imgURL,
            "name": product.name,
            "link": product.link,
            "quantitySold": product.quantitySold,
            "price": product.price,
            "reviewCount": product.reviewCount,
            "rating": product.rating,
            "sellerName": product.sellerName,
            "brandName": product.brandName
        }
        product['reviewSummary'] = '- Ưu điểm: Sản phẩm tốt<br>-Nhược điểm: Sản phẩm không tốt'
        return {"success": True, "data": product}, 200
        
def search_products_by_vector(vector, indexFile: str, k: int):
    """
    Search for products using a vector representation.

    This function searches for the top `k` products that are most similar to the given
    vector using a pre-built FAISS index. It retrieves the corresponding product
    details from the database.

    :param vector: The query vector used for searching.
    :param indexFile: The filename of the FAISS index to be used for the search.
    :param k: The number of top similar products to retrieve.

    :return: A list of dictionaries containing the product details such as productId,
             origin, imgURL, name, link, quantitySold, price, reviewCount, rating,
             sellerName, and brandName.
    """
    index_search = faiss.read_index(f'indices/{indexFile}')
    res = []

    D, I = index_search.search(vector, k)

    try:
        for i in I[0]:
            product = Product.Product.get_product_by_productId(int(i))
            if product:
                res.append({
                    "productId": product.productId,
                    "origin": product.origin,
                    "imgURL": product.imgURL,
                    "name": product.name,
                    "link": product.link,
                    "quantitySold": product.quantitySold,
                    "price": product.price,
                    "reviewCount": product.reviewCount,
                    "rating": product.rating,
                    "sellerName": product.sellerName,
                    "brandName": product.brandName
                })
    except Error as e:
        print(e)

    return res

@bp.route('/query/<string:query>')
def search_products_by_query(query: str):    
    """
    Search for products using a query string.

    This function encodes the query string into a vector representation and searches 
    for the top `k` products that are most similar to the query using a pre-built 
    FAISS index. It retrieves the corresponding product details from the database.

    :API: GET /api/product/query/<string:query>

    :param query: The query string used for searching.

    :return: 1 of the following cases:
    - Successful: {"success": True, "data": products}, 200
    - No products found: {"success": False, "message": "No products found."}, 404
    :dataformat: json with the following structure:
    [
        {
            "productId": int,
            "origin": string,
            "imgURL": string,
            "name": string,
            "link": string,
            "quantitySold": int,
            "price": float,
            "reviewCount": int,
            "rating": float,
            "sellerName": string,
            "brandName": string
        },
        ...
    ]
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    k = 120
    query_vector = model.encode(query)
    query_vector = query_vector.astype(np.float32).reshape(1, -1)

    res = search_products_by_vector(query_vector, 'search.index', k)
    
    body = request.get_json()
    order_by = body.get('order_by')
    type = body.get('type')
    if order_by == 'quantitySold':
        res = sorted(res, key=lambda x: x['quantitySold'], reverse=True if type == 'desc' else False)
    elif order_by == 'price':
        res = sorted(res, key=lambda x: x['price'], reverse=True if type == 'desc' else False)
    elif order_by == 'reviewCount':
        res = sorted(res, key=lambda x: x['reviewCount'], reverse=True if type == 'desc' else False)
    elif order_by == 'rating':
        res = sorted(res, key=lambda x: x['rating'], reverse=True if type == 'desc' else False)
    
    if res == []:
        return {"success": False, "message": "No products found."}, 404
    
    return {"success": True, "data": res}, 200

@bp.route('/recommend_products_by_history')
@login_required
def recommend_products_by_history():
    """
    Recommend products by given user's history.

    This function will take all products viewed by the given user and extract
    the following features: name, category names, origin, seller name, brand name,
    quantitySold, reviewCount, and rating. It will then use a pre-built FAISS index
    to find the top `k` products that are most similar to the given user's history.

    :API: GET /api/product/recommend_products_by_history

    :return: 1 of the following cases:
    - Successful: {"success": True, "data": res}, 200
    - No products found: {"success": False, "message": "No products found."}, 404
    :dataformat: json with the following structure: an array of products (except for the last page)
    [
        {
            "productId": int,
            "origin": string,
            "imgURL": string,
            "name": string,
            "link": string,
            "quantitySold": int,
            "price": float,
            "reviewCount": int,
            "rating": float,
            "sellerName": string,
            "brandName": string,
            "reviewSummary": string
        },
        ...
    ]
    """

    accountId = g.user.accountId
    model = SentenceTransformer('all-MiniLM-L6-v2')
    vectorizer = joblib.load('indices/vectorizer.joblib')
    svd = joblib.load('indices/svd.joblib')
    scaler = MinMaxScaler()
    k = 120

    products = ProductHistory.ProductHistory.get_product_histories_by_accountId(accountId)
    product_ids = []
    product_origins = []
    for p in products:
        product_ids.append(p.productId)
        product_origins.append(p.origin) 

    products = []

    try:
        for i in range(len(product_ids)):
            products.append(Product.Product.get_product_by_productId_origin(product_ids[i], product_origins[i]))
        names_categories = []
        metadata = []
        numerical_fields = []
        for p in products:
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

        names_categories = model.encode(names_categories)
        names_categories = names_categories.astype(np.float32)
        metadata = vectorizer.transform(metadata)
        metadata = svd.transform(metadata)
        metadata = np.array(metadata).astype(np.float32)
        numerical_fields = scaler.fit_transform(numerical_fields)
        numerical_fields = np.array(numerical_fields).astype(np.float32)

        combined_vectors = np.hstack((names_categories, metadata, numerical_fields))
        avg_vector = np.mean(combined_vectors, axis=0).reshape(1, -1)
        res = search_products_by_vector(avg_vector, 'recommendation.index', k)

    except Error as e:
        print(e)
        return {"success": False, "message": "No products found."}, 404

    if len(res) == 0:
        return {"success": False, "message": "No products found."}, 404
    return {"success": True, "data": res}, 200

@bp.route('/recommend_products_by_product_id/<string:origin>/<int:productId>')
def recommend_products_by_product_id(origin: str, productId: int):
    """
    Recommend products by given product id.

    :API: GET /api/product/recommend_products_by_product_id/<string:origin>/<int:productId>

    :param origin: The origin of the product, can be "tiki" or "lazada".
    :param productId: The id of the product.

    :return: 1 of the following cases:
    - Successful: {"success": True, "data": products}, 200
    - No products found: {"success": False, "message": "No products found."}, 404
    :dataformat: json with the following structure: a array with k products (except for the last page)
    [
        {
            "productId": int,
            "origin": string,
            "imgURL": string,
            "name": string,
            "quantitySold": int,
            "price": float,
            "reviewCount": int,
            "rating": float
        },
        ...
    ]
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    vectorizer = joblib.load('indices/vectorizer.joblib')
    svd = joblib.load('indices/svd.joblib')
    scaler = MinMaxScaler()
    k = 10

    try:
        product = Product.Product.get_product_by_productId_origin(productId, origin)
        name_category = product.name.strip() if product.name.strip().endswith(string.punctuation) else product.name.strip() + '.'
        categories = Category.Category.get_categories_by_productId_origin(productId, product.origin)
        for ci in range(len(categories)):
            if ci == 0:
                name_category += (' ' + categories[ci].name)
            else:
                name_category += (', ' + categories[ci].name)
            if ci == len(categories) - 1:
                name_category += '.'
        metadata =str.lower(product.origin) + ' ' + str.lower(product.sellerName.replace(' ', '')) + ' ' + str.lower(product.brandName.replace(' ', ''))
        numerical_fields = [product.quantitySold, product.reviewCount, product.rating]

        name_category = model.encode([name_category])
        name_category = name_category.astype(np.float32)
        metadata = vectorizer.transform([metadata])
        metadata = svd.transform(metadata)
        metadata = np.array(metadata).astype(np.float32)
        numerical_fields = scaler.fit_transform([numerical_fields])
        numerical_fields = np.array(numerical_fields).astype(np.float32)

        combined_vectors = np.hstack((name_category, metadata, numerical_fields)).reshape(1, -1)
        res = search_products_by_vector(combined_vectors, 'recommendation.index', k)

    except Error as e:
        print(e)
        return {"success": False, "message": "No products found."}, 404

    if len(res) == 0:
        return {"success": False, "message": "No products found."}, 404
    return {"success": True, "data": res}, 200
