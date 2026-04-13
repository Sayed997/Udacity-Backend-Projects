import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
uncomment the following line to initialize the datAbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()


# ROUTES
'''
endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def get_drinks():
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.short() for drink in drinks]

        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        }), 200

    except Exception:
        # Internal server error
        abort(500)


'''
endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in drinks]

        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        }), 200

    except Exception:
        abort(500)


'''
endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    if not body:
        abort(400)

    title = body.get('title', None)
    recipe = body.get('recipe', None)

    # Validate required fields
    if not title or not recipe:
        abort(422)

    try:
        # recipe must be stored as a JSON string
        drink = Drink(
            title=title,
            recipe=json.dumps(recipe)
        )

        drink.insert()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200

    except Exception:
        abort(422)


'''
implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    body = request.get_json()

    if not body:
        abort(400)

    drink = Drink.query.get(id)

    if not drink:
        abort(404)

    title = body.get('title', None)
    recipe = body.get('recipe', None)

    try:
        if title:
            drink.title = title

        if recipe:
            drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200

    except Exception:
        abort(422)


'''
implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.get(id)

    if not drink:
        abort(404)

    try:
        drink.delete()

        return jsonify({
            "success": True,
            "delete": id
        }), 200

    except Exception:
        abort(422)


# Error Handling
'''
error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
error handlers using the @app.errorhandler(error) decorator

'''

'''
error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    return jsonify({
        "success": False,
        "error": ex.status_code,
        "message": ex.error.get("description")
    }), ex.status_code
