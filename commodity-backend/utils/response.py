from flask import jsonify


def ok(data=None, message: str = "ok"):
    return jsonify({"code": 0, "message": message, "data": data}), 200


def err(message: str, code: int = 400, http_status: int = 400):
    return jsonify({"code": code, "message": message, "data": None}), http_status

