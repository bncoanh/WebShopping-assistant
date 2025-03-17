from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import requests

bp = Blueprint('main', __name__)
BASE_URL = 'https://127.0.0.1:5000'

@bp.route('/')
def index():
    tiki_res = requests.request('GET', BASE_URL + '/api/product/tiki/get_categories', verify=False).json()
    lazada_res = requests.request('GET', BASE_URL + '/api/product/lazada/get_categories', verify=False).json()
    categories_tiki = []
    categories_lazada = []
    for category in tiki_res['data']:
        categories_tiki.append({'categoryId': category['categoryId'], 'name': category['name']})
    for category in lazada_res['data']:
        categories_lazada.append({'categoryId': category['categoryId'], 'name': category['name']})
    recommended_products = []
    error = None
    if g.username:
        backend_session = requests.Session()
        headers = {'Content-Type': 'application/json'}
        payload = {'username': g.username, 'password': g.password}
        backend_session.request('POST', BASE_URL + '/api/auth/login', headers=headers, json=payload, verify=False)
        res = backend_session.request('GET', BASE_URL + '/api/product/recommend_products_by_history', verify=False)
        if res.status_code == 401:
            error = 'Bạn cần đăng nhập lại để xem các sản phẩm đề xuất'
        elif res.status_code == 404:
            res = requests.request('GET', BASE_URL + '/api/product/recommend_products', verify=False)
            if res.status_code == 404:
                error = 'Không tìm thấy sản phẩm đề xuất nào'
            elif res.status_code != 200:
                error = 'Lỗi hệ thống'
        elif res.status_code == 500:
            error = 'Lỗi hệ thống'
    else:
        res = requests.request('GET', BASE_URL + '/api/product/recommend_products', verify=False)
        if res.status_code == 404:
            error = 'Không tìm thấy sản phẩm đề xuất nào'
        elif res.status_code != 200:
            error = 'Lỗi hệ thống'
    
    if not error:
        res = res.json()
        recommended_products = res['data']
        for p in recommended_products:
            p['price'] = '{:,.0f}'.format(float(p['price']))
    else:
        flash(error)
    return render_template('main/index.html', categories_tiki=categories_tiki, categories_lazada=categories_lazada, recommended_products=recommended_products)

@bp.route('/category/<string:origin>/<int:categoryId>/<string:name>/<int:page>', methods=('GET', 'POST'))
def category(origin, categoryId, name, page):
    if request.method == 'POST':
        order_by = request.form['order_by']
        type = request.form['type']
        return redirect(url_for('main.category', origin=origin, categoryId=categoryId, page=1, order_by=order_by, type=type, name=name))
    
    tiki_res = requests.request('GET', BASE_URL + '/api/product/tiki/get_categories', verify=False).json()
    lazada_res = requests.request('GET', BASE_URL + '/api/product/lazada/get_categories', verify=False).json()
    categories_tiki = []
    categories_lazada = []
    for category in tiki_res['data']:
        categories_tiki.append({'categoryId': category['categoryId'], 'name': category['name']})
    for category in lazada_res['data']:
        categories_lazada.append({'categoryId': category['categoryId'], 'name': category['name']})
    
    order_by = request.args.get('order_by', 'normal')
    type = request.args.get('type', 'asc')
    payload = {'order_by': order_by, 'type': type}
    headers = {'Content-Type': 'application/json'}

    products = []
    res = requests.request('GET', BASE_URL + f'/api/product/{origin}/category/{categoryId}/{page}', json=payload, headers=headers, verify=False)
    if res.status_code == 200:
        res = res.json()
        products = res['data']
        for p in products:
            p['price'] = '{:,.0f}'.format(float(p['price']))

        return render_template('main/category.html', categories_tiki=categories_tiki, categories_lazada=categories_lazada, products=products, origin=origin, categoryId=categoryId, name=name, current_page=res['current_page'], max_page=res['max_page'], total_products=res['total_products'], order_by=order_by, type=type)
    else:
        flash("Không có sản phẩm nào thuộc danh mục này.")
        return render_template('main/category.html', categories_tiki=categories_tiki, categories_lazada=categories_lazada, products=products, name=name)

@bp.route('/product/<string:origin>/<int:productId>', methods=('GET', 'POST'))
def product(origin, productId):
    tiki_res = requests.request('GET', BASE_URL + '/api/product/tiki/get_categories', verify=False).json()
    lazada_res = requests.request('GET', BASE_URL + '/api/product/lazada/get_categories', verify=False).json()
    categories_tiki = []
    categories_lazada = []
    for category in tiki_res['data']:
        categories_tiki.append({'categoryId': category['categoryId'], 'name': category['name']})
    for category in lazada_res['data']:
        categories_lazada.append({'categoryId': category['categoryId'], 'name': category['name']})
    recommended_products = []
    product = None
    error = None

    product = requests.request('GET', BASE_URL + f'/api/product/{origin}/product/{productId}', verify=False)
    product = product.json()['data']
    product['price'] = '{:,.0f}'.format(float(product['price']))
    
    res = requests.request('GET', BASE_URL + f'/api/product/recommend_products_by_product_id/{origin}/{productId}', verify=False)
    if res.status_code == 404:
        error = 'Không tìm thấy sản phẩm tương tự nào'
    elif res.status_code != 200:
        error = 'Lỗi hệ thống'

    if not error:
        res = res.json()
        recommended_products = res['data']
        for p in recommended_products:
            p['price'] = '{:,.0f}'.format(float(p['price']))
    else:
        flash(error)
    return render_template('main/product.html', recommended_products=recommended_products, product=product, categories_tiki=categories_tiki, categories_lazada=categories_lazada)

@bp.route('/track_product/<string:origin>/<int:productId>', methods=('POST',))
def track_product(origin, productId):
    if g.username is not None:
        backend_session = requests.Session()
        headers = {'Content-Type': 'application/json'}
        payload = {'username': g.username, 'password': g.password}
        backend_session.request('POST', BASE_URL + '/api/auth/login', headers=headers, json=payload, verify=False)
        res = backend_session.request('POST', BASE_URL + f'/api/tracking/product/{origin}/{productId}', verify=False)
        if res.status_code != 200:
            return {'success': False, 'message': 'Không lưu được sản phẩm'}, res.status_code
        else:
            return {'success': True, 'message': 'Lưu được sản phẩm'}, 200
    else:
        return {'success': False, 'message': 'Vui lòng đăng nhập'}, 401
    
@bp.route('/search', methods=('GET', 'POST'))
def search():
    query = request.args.get('query')
    if request.method == 'POST':
        order_by = request.form['order_by']
        type = request.form['type']
        return redirect(url_for('main.search', order_by=order_by, type=type, query=query))
    
    tiki_res = requests.request('GET', BASE_URL + '/api/product/tiki/get_categories', verify=False).json()
    lazada_res = requests.request('GET', BASE_URL + '/api/product/lazada/get_categories', verify=False).json()
    categories_tiki = []
    categories_lazada = []
    for category in tiki_res['data']:
        categories_tiki.append({'categoryId': category['categoryId'], 'name': category['name']})
    for category in lazada_res['data']:
        categories_lazada.append({'categoryId': category['categoryId'], 'name': category['name']})
    
    order_by = request.args.get('order_by', 'normal')
    type = request.args.get('type', 'asc')
    payload = {'order_by': order_by, 'type': type}
    headers = {'Content-Type': 'application/json'}

    products = []
    res = requests.request('GET', BASE_URL + f'/api/product/query/{query}', json=payload, headers=headers, verify=False)
    if res.status_code == 200:
        res = res.json()
        products = res['data'] 
        for p in products:
            p['price'] = '{:,.0f}'.format(float(p['price']))

        return render_template('main/search.html', categories_tiki=categories_tiki, categories_lazada=categories_lazada, query=query, products=products, order_by=order_by, type=type)
    elif res.status_code == 404:
        flash("Không có sản phẩm nào liên quan tới từ khoá bạn tìm")
        return render_template('main/search.html', categories_tiki=categories_tiki, categories_lazada=categories_lazada, products=products, query=query)
    else:
        flash("Lỗi hệ thống")
        return render_template('main/search.html', categories_tiki=categories_tiki, categories_lazada=categories_lazada, products=products, query=query)