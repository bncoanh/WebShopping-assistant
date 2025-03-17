import functools
from flask import (
    Blueprint, g, request, session
)
from werkzeug.security import check_password_hash, generate_password_hash
from mysql.connector import Error
from .models import *

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=('POST',))
def register():
    """
    Register a new user.

    :API: POST /api/auth/register

    The request body should be a JSON object with the following structure:
    {
        "username": string,
        "password": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Register successful!"}, 201
    - Username or password is required: {"success": False, "message": "Username/Password is required."}, 409
    - User is already registered: {"success": False, "message": "User <username> is already registered."}, 409
    """

    if request.method == 'POST':
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                Account.Account(username=username, password=password, isAdmin=False).add()
            except Error:
                error = f"User {username} is already registered."
            else:
                return {'success': True, 'message': 'Register successful!'}, 201
        
        return {'success': False, 'message': error}, 409

@bp.route('/login', methods=('POST',))
def login():
    """
    Log in with the provided username and password.

    :API: POST /api/auth/login

    The request body should be a JSON object with the following structure:
    {
        "username": string,
        "password": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Log in successful!"}, 200
    - Incorrect username or password: {"success": False, "message": "Incorrect username or password"}, 401
    """
    if request.method == 'POST':
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        error = None
        account = Account.Account.get_account_by_username_password(username, password)

        if account is None:
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['accountId'] = account.accountId
            return {'success': True, 'message': 'Log in successful!'}, 200

        return {"success": False, "message": error}, 401
    
@bp.before_app_request
def load_logged_in_user():
    """Load the user associated with the current session.

    If the user is not logged in (i.e. there is no accountId in the session),
    then g.user is set to None. Otherwise, g.user is set to the user with
    the matching accountId.

    :return: None
    """
    accountId = session.get('accountId')

    if accountId is None:
        g.user = None
    else:
        account = Account.Account.get_account_by_accountId(accountId)
        g.user = account

def login_required(view):
    """Check if the user is logged in.

    If the user is not logged in (i.e. there is no g.user), then return a 401
    response with a JSON body of {"success": False, "message": "You are not
    logged in."}. Otherwise, call the original view.

    :param view: The original view to be wrapped.
    :return: The result of calling the original view if the user is logged in,
             otherwise a 401 response with a JSON body.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return {'success': False, 'message': 'You are not logged in.'}, 401

        return view(**kwargs)

    return wrapped_view

@bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user/admin.

    :API: GET /api/auth/logout

    :return: {"success": True, "message": "Log out successful!"}, 200
    """

    session.clear()
    return {'success': True, 'message': 'Log out successful!'}, 200

@bp.route('/change_password', methods=('PATCH',))
@login_required
def change_password():
    """
    Change the password of the current user.

    :API: PATCH /api/auth/change_password

    The request body should be a JSON object with the following structure:
    {
        "oldPassword": string,
        "newPassword": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Change password successful!"}, 200
    - Old password is incorrect: {"success": False, "message": "Incorrect old password."}, 401
    """
    if request.method == 'PATCH':
        data = request.get_json()
        oldPassword = data.get('oldPassword')
        newPassword = data.get('newPassword')
        accountId = g.user.accountId
        password = g.user.password

        error = None
        if not check_password_hash(password, oldPassword):
            error = 'Incorrect old password.'

        if error is None:
            Account.Account.update_password_by_accountId(newPassword, accountId)
            g.user.password = generate_password_hash(newPassword)
            return {'success': True, 'message': 'Change password successful!'}, 200
    
        return {'success': False, 'message': error}, 401

@bp.route('/admin_login', methods=('POST',))
def admin_login():
    """
    Log in as an admin with the provided username and password.

    :API: POST /api/auth/admin_login

    The request body should be a JSON object with the following structure:
    {
        "username": string,
        "password": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Log in as an admin successful!"}, 200
    - Incorrect username or password: {"success": False, "message": "Incorrect username or password."}, 401
    - Not an admin: {"success": False, "message": "You cannot log in as an admin."}, 401
    """
    if request.method == 'POST':
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        error = None
        account = Account.Account.get_account_by_username_password(username, password)

        if account is None:
            error = 'Incorrect username or password.'
        elif account.isAdmin == False:
            error = 'You cannot log in as an admin.'

        if error is None:
            session.clear()
            session['accountId'] = account.accountId
            return {'success': True, 'message': 'Log in as an admin successful!'}, 200

        return {"success": False, "message": error}, 401

def admin_login_required(view):
    """
    Check if the user is logged in and is an admin.

    If the user is not logged in (i.e. there is no g.user), then return a 401
    response with a JSON body of {"success": False, "message": "You are not
    logged in."}. If the user is logged in but is not an admin, then return a
    401 response with a JSON body of {"success": False, "message": "You are
    not an admin."}. Otherwise, call the original view.

    :param view: The original view to be wrapped.
    :return: The result of calling the original view if the user is logged in
             and is an admin, otherwise a 401 response with a JSON body.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return {'success': False, 'message': 'You are not logged in.'}, 401
        elif g.user.isAdmin == 0:
            return {'success': False, 'message': 'You are not an admin.'}, 401

        return view(**kwargs)

    return wrapped_view