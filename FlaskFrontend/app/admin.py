from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import requests

bp = Blueprint('admin', __name__, url_prefix='/admin')
BASE_URL = 'https://127.0.0.1:5000'

@bp.route('/', methods=('GET', ))
def index():
    return render_template('admin/index.html')

@bp.route('/users_management', methods=('GET', ))
def users_management():
    backend_session = requests.Session()
    users = []
    if g.username and g.is_admin:
        payload = {'username': g.username, 'password': g.password}
        headers = {'Content-Type': 'application/json'}
        backend_session.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
        res = backend_session.request('GET', BASE_URL + '/api/admin/manage_users', verify=False)
        if res.status_code == 200:
            res = res.json()
            users = res['data']
    
    error = request.args.get('error')
    success_message = request.args.get('success_message', None)
    if error:
        flash(error)

    return render_template('admin/users_management.html', users=users, success_message=success_message)

@bp.route('/add_user')
def add_user():
    backend_session = requests.Session()
    error = None
    if g.username and g.is_admin:
        payload = {'username': g.username, 'password': g.password}
        headers = {'Content-Type': 'application/json'}
        backend_session.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
        username = request.args.get('username')
        password = request.args.get('password')
        payload = {'username': username, 'password': password}
        res = backend_session.request('POST', BASE_URL + '/api/admin/manage_users', headers=headers, json=payload, verify=False)
        if res.status_code == 409:
            error = f'Người dùng {username} đã được đăng ký trước đó'
        elif res.status_code != 201:
            error = 'Lỗi hệ thống'
        if error is None:
            return redirect(url_for('admin.users_management', success_message=f'Người dùng {username} đã được đăng ký'))

    return redirect(url_for('admin.users_management', error=error))

@bp.route('/change_user')
def change_user():
    backend_session = requests.Session()
    error = None
    if g.username and g.is_admin:
        payload = {'username': g.username, 'password': g.password}
        headers = {'Content-Type': 'application/json'}
        backend_session.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
        accountId = request.args.get('accountId')
        password = request.args.get('password')
        payload = {'accountId': int(accountId), 'password': password}
        res = backend_session.request('PATCH', BASE_URL + '/api/admin/manage_users', headers=headers, json=payload, verify=False)
        if res.status_code == 404:
            error = 'Không tìm thấy người dùng'
        elif res.status_code != 200:
            error = 'Lỗi hệ thống'
        if error is None:
            return redirect(url_for('admin.users_management', success_message=f'Người dùng có ID {accountId} đã được cập nhật'))

    return redirect(url_for('admin.users_management', error=error))

@bp.route('/delete_user')
def delete_user():
    backend_session = requests.Session()
    error = None
    if g.username and g.is_admin:
        payload = {'username': g.username, 'password': g.password}
        headers = {'Content-Type': 'application/json'}
        backend_session.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
        accountId = request.args.get('accountId')
        payload = {'accountId': int(accountId)}
        res = backend_session.request('DELETE', BASE_URL + '/api/admin/manage_users', headers=headers, json=payload, verify=False)
        if res.status_code == 404:
            error = 'Không tìm thấy người dùng'
        elif res.status_code != 200:
            error = 'Lỗi hệ thống'
        if error is None:
            return redirect(url_for('admin.users_management', success_message=f'Người dùng có ID {accountId} đã được xoá'))

    return redirect(url_for('admin.users_management', error=error))

@bp.route('/update_data', methods=('GET', 'POST'))
def update_data():
    error = None
    success_message = None
    if request.method == 'POST':
        action = request.form['action']
        if not action:
            error = "Thiếu thông tin hành động"
        else:
            backend_session = requests.Session()
            payload = {'username': g.username, 'password': g.password}
            headers = {'Content-Type': 'application/json'}
            backend_session.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
            try:
                if action == 'crawl_tiki':
                    res = backend_session.request('POST', BASE_URL + '/api/data/crawl_tiki', verify=False)
                    if res.status_code != 201:
                        raise Exception('Lỗi khi crawl dữ liệu Tiki')
                    else:
                        success_message = 'Crawl dữ liệu Tiki thành công'
                elif action == 'crawl_lazada':
                    res = backend_session.request('POST', BASE_URL + '/api/data/crawl_lazada', verify=False)
                    if res.status_code != 201:
                        raise Exception('Lỗi khi crawl dữ liệu Lazada')
                    else:
                        success_message = 'Crawl dữ liệu Lazada thành công'
                elif action == 'load_tiki':
                    res = backend_session.request('POST', BASE_URL + '/api/data/load_tiki', verify=False)
                    if res.status_code == 404:
                        raise Exception('Không tìm thấy dữ liệu Tiki để cập nhật')
                    elif res.status_code == 409:
                        raise Exception('Không thể tải dữ liệu Tiki vào cơ sở dữ liệu')
                    elif res.status_code != 201:
                        raise Exception('Lỗi hệ thống')
                    else:
                        success_message = 'Cập nhật dữ liệu Tiki thành công'
                elif action == 'load_lazada':
                    res = backend_session.request('POST', BASE_URL + '/api/data/load_lazada', verify=False)
                    if res.status_code == 404:
                        raise Exception('Không tìm thấy dữ liệu Lazada để cập nhật')
                    elif res.status_code == 409:
                        raise Exception('Không thể tải dữ liệu Lazada vào cơ sở dữ liệu')
                    elif res.status_code != 201:
                        raise Exception('Lỗi hệ thống')
                    else:
                        success_message = 'Cập nhật dữ liệu Lazada thành công'
                elif action == 'create_index':
                    res = backend_session.request('POST', BASE_URL + '/api/data/create_index', verify=False)
                    if res.status_code == 409:
                        raise Exception('Không thể lấy dữ liệu từ cơ sở dữ liệu')
                    elif res.status_code != 201:
                        raise Exception('Lỗi hệ thống')
                    else:
                        success_message = 'Tạo index thành công'
                else:
                    error = 'Hành động không hợp lệ'
                
            except Exception as e:
                error = 'Đã có lỗi xảy ra: ' + str(e)
    
    if error:
        flash(error)
        return render_template('admin/update_data.html')
    else:
        return render_template('admin/update_data.html', success_message=success_message)