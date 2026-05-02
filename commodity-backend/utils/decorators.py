from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt() or {}
        if claims.get("role") != "admin":
            return jsonify({"code": 403, "message": "需要管理员权限", "data": None}), 403
        return fn(*args, **kwargs)

    return wrapper


def user_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt() or {}
        if claims.get("role") != "user":
            return jsonify({"code": 403, "message": "需要普通用户权限", "data": None}), 403
        return fn(*args, **kwargs)

    return wrapper

