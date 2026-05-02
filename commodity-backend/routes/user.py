from flask import Blueprint
from flask_jwt_extended import jwt_required

from services.absa_service import analyze_product
from utils.decorators import user_required
from utils.response import err, ok

# bp = Blueprint("user", __name__, url_prefix="/user")
bp = Blueprint("user", __name__)


@bp.route("/products/<int:product_id>", methods=["GET"])
@jwt_required()
@user_required
def product_absa(product_id: int):
    result = analyze_product(product_id)
    if result.get("error") == "product_not_found":
        return err("商品不存在", code=404, http_status=404)
    return ok(result)

