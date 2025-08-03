import os
from pymongo import MongoClient, ReturnDocument
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

# 从 .env 加载配置
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['ham_radio_quiz']

# --- 数据库集合 ---
users_collection = db['users']
questions_collection = db['questions']

# --- 用户操作 ---
def add_user(username, password):
    """添加新用户"""
    if users_collection.find_one({"username": username}):
        return None  # 用户已存在
    hashed_password = generate_password_hash(password)
    user = {"username": username, "password": hashed_password, "progress": {}}
    result = users_collection.insert_one(user)
    return result.inserted_id

def find_user_by_username(username):
    """根据用户名查找用户"""
    return users_collection.find_one({"username": username})

def check_user_password(user, password):
    """检查用户密码"""
    return check_password_hash(user['password'], password)

def get_user_by_id(user_id):
    """根据ID查找用户"""
    return users_collection.find_one({"_id": ObjectId(user_id)})

# --- 题目操作 ---
def get_questions(category, projection=None):
    """获取指定分类的题目"""
    return list(questions_collection.find({"category": category}, projection))
    
def get_question_by_jid(jid):
    """根据J_ID获取单个问题"""
    return questions_collection.find_one({"J_ID": jid})

# --- 进度操作 ---
def get_user_progress(user_id, category):
    """获取用户的练习进度和错题集"""
    user = get_user_by_id(user_id)
    if not user: return None
    
    category_progress = user.get("progress", {}).get(category, {})
    return {
        "sequential": category_progress.get("sequential", {}),
        "wrong_ids": category_progress.get("wrong_ids", [])
    }

def update_user_progress(user_id, category, question_jid, is_correct):
    """更新用户的练习进度和错题集"""
    status = "correct" if is_correct else "incorrect"
    
    # 更新顺序练习进度
    update_query = {f"progress.{category}.sequential.{question_jid}": status}
    
    # 更新错题集
    if is_correct:
        # 如果答对，从错题集中移除
        update_query[f"$pull"] = {f"progress.{category}.wrong_ids": question_jid}
    else:
        # 如果答错，添加到错题集（如果不存在）
        update_query[f"$addToSet"] = {f"progress.{category}.wrong_ids": question_jid}

    updated_user = users_collection.find_one_and_update(
        {"_id": ObjectId(user_id)},
        update_query,
        return_document=ReturnDocument.AFTER
    )
    return updated_user is not None