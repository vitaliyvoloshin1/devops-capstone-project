"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based on the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################

# ... place you code here to LIST accounts ...


######################################################################
# READ AN ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(account_id):
    """
    Reads an Account
    This endpoint will read an Account based on the account_id that is requested
    """
    app.logger.info("Request to read an Account with id: %s", account_id)

    # Находим аккаунт
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id [{account_id}] could not be found.")

    return account.serialize(), status.HTTP_200_OK


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """
    Update an Account
    This endpoint will update an existing Account
    """
    app.logger.info("Request to update Account with id: %s", account_id)

    # Проверяем, существует ли аккаунт
    account = Account.find(account_id)
    if not account:
        app.logger.error(f"Account with id {account_id} not found.")
        abort(status.HTTP_404_NOT_FOUND, f"Account with id [{account_id}] not found.")

    # Проверяем Content-Type
    check_content_type("application/json")

    # Получаем данные из запроса
    account_data = request.get_json()

    # Логируем входные данные
    app.logger.info(f"Received JSON payload for update: {account_data}")

    # Проверяем, что данные переданы
    if not account_data or not isinstance(account_data, dict):
        app.logger.error("Invalid JSON data provided.")
        abort(status.HTTP_400_BAD_REQUEST, "Invalid JSON data provided")

    # Проверяем, содержит ли `account_data` хотя бы одно поле для обновления
    valid_fields = ["name", "email", "address", "phone_number", "date_joined"]
    if not any(key in account_data for key in valid_fields):
        app.logger.error("No valid fields provided for update.")
        abort(status.HTTP_400_BAD_REQUEST, "No valid fields provided for update")

    # Обновляем поля
    for key in valid_fields:
        if key in account_data:
            setattr(account, key, account_data[key])
            app.logger.info(f"Updating {key}: {account_data[key]}")

    # ✅ Теперь вызываем `update()`, а не `save()`
    account.update()
    app.logger.info(f"Updated account: {account.serialize()}")

    return account.serialize(), status.HTTP_200_OK



######################################################################
# DELETE AN ACCOUNT
######################################################################

# ... place you code here to DELETE an account ...


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
