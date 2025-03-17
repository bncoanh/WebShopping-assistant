from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from app.auth import admin_login_required
from mysql.connector import Error
import requests
from .models import *

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/manage_users', methods=('GET', 'POST', 'PATCH', 'DELETE'))
@admin_login_required
def manage_users():
    """
    Manage users

    :API: GET/POST/PATCH/DELETE /api/admin/manage_users

    :GET: Get all users

    :return: 1 of the following cases:
    - Successful: {"success": True, "data": users}, 200
    :dataformat: json with the following structure:
    {
        "accountId": int,
        "username": string,
        "password": string
    } 

    :POST: Register a new user

    The request body should be a JSON object with the following structure:
    {
        "username": string,
        "password": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Register successful!"}, 201
    - Username or password is required: {"success": False, "message": "Username/Password is required."}, 409
    - User is already registered: {"success": False, "message": "User <username> is already registered."}, 409

    :PATCH: Update an existing user

    The request body should be a JSON object with the following structure:
    {
        "accountId": int,
        "password": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Update user successful!"}, 200
    - User not found: {"success": False, "message": "User not found."}, 404

    :DELETE: Delete an existing user

    The request body should be a JSON object with the following structure:
    {
        "accountId": int
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Delete user successful!"}, 200
    - User not found: {"success": False, "message": "User not found."}, 404

    """
    if request.method == 'GET':
        users = None

        users = Account.Account.get_users()
        data = []
        for u in users:
            data.append({
                'accountId': u.accountId,
                'username': u.username,
                'password': u.password
            })

        return {'success': True, 'data': data}, 200

    if request.method == 'POST':
        data = request.get_json()
        res = requests.post('http://127.0.0.1:5000/api/auth/register', json=data)
        
        return res.json(), res.status_code

    if request.method == 'PATCH':
        data = request.get_json()

        accountId = data.get('accountId')
        password = data.get('password')

        if Account.Account.get_user_by_accountId(accountId) is None:
            return {'success': False, 'message': 'User not found.'}, 404

        Account.Account.update_password_by_accountId(password, accountId)

        return {'success': True, 'message': 'Update user successful!'}, 200

    if request.method == 'DELETE':
        data = request.get_json()

        accountId = data.get('accountId')

        if Account.Account.get_user_by_accountId(accountId) is None:
            return {'success': False, 'message': 'User not found.'}, 404

        Account.Account.delete_user_by_accountId(accountId)

        return {'success': True, 'message': 'Delete user successful!'}, 200
    
