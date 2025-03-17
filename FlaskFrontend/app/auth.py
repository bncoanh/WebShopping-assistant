import functools, requests

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')
BASE_URL = 'https://127.0.0.1:5000'

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repeat_password = request.form['repeat-password']
        error = None

        if repeat_password != password:
            error = 'Mật khẩu nhập lại không chính xác'
        if not username:
            error = 'Cần phải nhập tên người dùng'
        elif not password:
            error = 'Cần phải nhập mật khẩu'

        if error is None:
            payload = {'username': username, 'password': password}
            headers = {'Content-Type': 'application/json'}
            res = requests.request('POST', BASE_URL + '/api/auth/register', headers=headers, json=payload, verify=False)
            if res.status_code == 500:
                error = 'Lỗi hệ thống'
            else:
                res = res.json()
                if res['success'] == True:
                    return redirect(url_for("auth.login"))
                elif res['success'] == False:
                    error = f'Người dùng {username} đã được đăng ký'

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            payload = {'username': username, 'password': password}
            headers = {'Content-Type': 'application/json'}
            res = requests.request('POST', BASE_URL + '/api/auth/login', headers=headers, json=payload, verify=False)
            if res.status_code == 500:
                error = 'Lỗi hệ thống'
            else:
                res = res.json()
                if res['success'] == True:
                    session['username'] = username
                    session['password'] = password
                    return redirect(url_for("index"))
                elif res['success'] == False:
                    error = 'Sai tên tài khoản hoặc mật khẩu'

        flash(error)

    return render_template('auth/login.html')

@bp.route('/admin_login', methods=('GET', 'POST'))
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            payload = {'username': username, 'password': password}
            headers = {'Content-Type': 'application/json'}
            res = requests.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
            if res.status_code == 500:
                error = 'Lỗi hệ thống'            
            else:
                res = res.json()
                if res['success'] == True:
                    session['username'] = username
                    session['password'] = password
                    session['is_admin'] = True
                    return redirect(url_for("admin.index"))
                elif res['success'] == False:
                    if res['message'] == 'Incorrect username or password.':
                        error = 'Sai tên tài khoản hoặc mật khẩu'
                    elif res['message'] == 'You cannot log in as an admin.':
                        error = 'Bạn không thể đăng nhập người quản trị'

        flash(error)

    return render_template('admin/login.html')

@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')
    password = session.get('password')
    is_admin = session.get('is_admin')

    if username is None:
        g.username = None
        g.password = None
    else:
        g.username = username
        g.password = password
        g.is_admin = is_admin


@bp.route('/logout')
def logout():
    is_admin = g.is_admin
    session.clear()
    if not is_admin:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('admin.index'))

@bp.route('/change_password', methods=('GET', 'POST'))
def change_password():
    if request.method == 'POST':
        old_password = request.form['old-password']
        new_password = request.form['new-password']
        repeat_password = request.form['repeat-password']
        error = None

        if repeat_password != new_password:
            error = 'Mật khẩu nhập lại không chính xác'
        if not old_password:
            error = 'Cần phải nhập mật khẩu cũ'
        elif not new_password:
            error = 'Cần phải nhập mật khẩu mới'

        if error is None:
            backend_session = requests.Session()
            headers = {'Content-Type': 'application/json'}
            payload = {'username': g.username, 'password': old_password}
            backend_session.request('POST', BASE_URL + '/api/auth/login', headers=headers, json=payload, verify=False)
            payload = {'oldPassword': old_password, 'newPassword': new_password}
            res = backend_session.request('PATCH', BASE_URL + '/api/auth/change_password', headers=headers, json=payload, verify=False)
            if res.status_code == 500:
                error = "Lỗi hệ thống"
            else:
                res = res.json()
                if res['success'] == True:
                    session['password'] = new_password
                    return redirect(url_for("index"))
                elif res['success'] == False:
                    error = 'Sai mật khẩu cũ'
            
        flash(error)

    return render_template('auth/change_password.html')

@bp.route('/admin_change_password', methods=('GET', 'POST'))
def admin_change_password():
    if request.method == 'POST':
        old_password = request.form['old-password']
        new_password = request.form['new-password']
        repeat_password = request.form['repeat-password']
        error = None

        if repeat_password != new_password:
            error = 'Mật khẩu nhập lại không chính xác'
        if not old_password:
            error = 'Cần phải nhập mật khẩu cũ'
        elif not new_password:
            error = 'Cần phải nhập mật khẩu mới'

        if error is None:
            backend_session = requests.Session()
            headers = {'Content-Type': 'application/json'}
            payload = {'username': g.username, 'password': old_password}
            backend_session.request('POST', BASE_URL + '/api/auth/admin_login', headers=headers, json=payload, verify=False)
            payload = {'oldPassword': old_password, 'newPassword': new_password}
            res = backend_session.request('PATCH', BASE_URL + '/api/auth/change_password', headers=headers, json=payload, verify=False)
            if res.status_code == 500:
                error = "Lỗi hệ thống"
            else: 
                res = res.json()
                if res['success'] == True:
                    session['password'] = new_password
                    return redirect(url_for("admin.index"))
                elif res['success'] == False:
                    error = 'Sai mật khẩu cũ'
            
        flash(error)

    return render_template('admin/change_password.html')