from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from models import User, db
from utils.response import err, ok
from utils.security import hash_password, verify_password

# bp = Blueprint("auth", __name__, url_prefix="/auth")
bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return err("用户名和密码不能为空")

    user = User.query.filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return err("账号或密码错误", code=401, http_status=401)

    if user.status != "active":
        return err("账号已被禁用", code=403, http_status=403)

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )
    return ok({"token": token, "userInfo": user.to_public_dict()})


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip() or None

    if not username:
        return err("用户名不能为空")
    if len(password) < 6:
        return err("密码至少 6 位")
    if User.query.filter(User.username == username).first():
        return err("用户名已存在")

    try:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role="user",
            phone=phone,
            status="active",
        )
        db.session.add(user)
        db.session.commit()
        return ok(None, "注册成功")
    except Exception as e:
        db.session.rollback()
        return err(f"注册失败：{str(e)}", code=500, http_status=500)


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = db.session.get(User, int(uid)) if str(uid).isdigit() else None
    if not user:
        return err("用户不存在", code=401, http_status=401)
    return ok(user.to_public_dict())

