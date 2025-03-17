from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from app.auth import login_required
from mysql.connector import Error
from .models import *
from datetime import datetime

bp = Blueprint('tracking', __name__, url_prefix='/api/tracking')

@bp.route('/browse', methods=('POST',))
@login_required
def browse():
    """
    Save the browse history of the users. Browse histories come from the search query

    :API: POST /api/tracking/browse

    The request body should be a JSON object with the following structure:
    {
        "browse": string
    }

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Save browse history successful!"}, 200
    """
    if request.method == 'POST':
        data = request.get_json()

        browse = data.get('browse')

        BrowseHistory.BrowseHistory(content=browse, accountId=g.user.accountId, createAt=datetime.now()).add()

        return {'success': True, 'message': 'Save browse history successful!'}, 200
    
@bp.route('/product/<string:origin>/<int:product_id>', methods=('POST',))
@login_required
def product(origin: str, product_id: int):
    """
    Save the product id that user browsed the original link.

    :API: POST /api/tracking/product/<string:origin>/<int:product_id>

    :param origin: The origin of the product, can be "tiki" or "lazada".
    :param product_id: The id of the product.

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Save product history successful!"}, 200
    - Failed to put the data into the database: {"success": False, "message": "Failed to put the data into the database."}, 409
    """
    if request.method == 'POST':
        
        try:

            ProductHistory.ProductHistory(accountId=g.user.accountId, productId=product_id, origin=origin, createAt=datetime.now()).add()
        except Error as e:
            print(e)
            return {'success': False, 'message': 'Failed to put the data into the database.'}, 409

        return {'success': True, 'message': 'Save product history successful!'}, 200

@bp.route('/recently_browsed')
@login_required
def recently_browsed():
    """
    Get the recently browsed products of the current user.

    :API: GET /api/tracking/recently_browsed

    :return: 1 of the following cases:
    - Successful: {"success": True, "message": "Get recently browsed products successful!", "data": data}, 200
    :dataformat: json with the following structure: a array of 10 browse history (except for the last page)
    [
        {
            "browseId": int,
            "content": string,
            "createAt": datetime
        },
        ...
    ]
    """
    
    histories = BrowseHistory.BrowseHistory.get_10_histories_by_accountId(g.user.accountId)

    data = []
    for h in histories:
        data.append({
            'browseId': h.browseId,
            'content': h.content,
            'createAt': h.createAt
        })

    return {'success': True, 'message': 'Get recently browsed products successful!', 'data': data}, 200