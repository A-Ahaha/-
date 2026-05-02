import csv
from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from models import Product, Comment, db
from services.absa_service import analyze_product
from utils.response import err, ok
from utils.decorators import admin_required

bp = Blueprint("upload", __name__, url_prefix="/upload")


@bp.route("/csv", methods=["POST"])
@jwt_required()
@admin_required
def upload_csv():
    if "file" not in request.files:
        return err("未上传文件")

    file = request.files["file"]

    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(content.splitlines())

        product = None
        count = 0

        for row in reader:
            product_name = row.get("商品")

            # 获取或创建商品
            if not product:
                product = Product.query.filter_by(name=product_name).first()
                if not product:
                    product = Product(name=product_name, sku=product_name)
                    db.session.add(product)
                    db.session.flush()

            comment = Comment(
                product_id=product.id,
                username=row.get("昵称"),
                content=row.get("评论"),
                rating=int(row.get("评分", 5)),
                created_at=datetime.strptime(row.get("日期"), "%Y-%m-%d %H:%M:%S"),
            )

            db.session.add(comment)
            count += 1

        db.session.commit()

        # ⭐ 核心：自动触发 ABSA + Issue 生成
        analyze_product(product.id)

        return ok({"count": count}, "上传 + 分析完成")

    except Exception as e:
        db.session.rollback()
        return err(f"上传失败: {str(e)}", 500, 500)