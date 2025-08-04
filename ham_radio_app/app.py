import os
import random
from flask import Flask, jsonify, request, g, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import database as db
from utils import create_token, token_required

# 加载环境变量
load_dotenv()

app = Flask(__name__)
# 允许所有来源的跨域请求，方便本地开发
CORS(app) 

# NEW: Add a route to serve the frontend application
@app.route('/')
def serve_app():
    """
    Serves the main index.html file which is the entry point of our frontend app.
    Flask will automatically look for this file in the 'templates' folder.
    """
    return render_template('index.html')
# --- 用户认证 API ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    user_id = db.add_user(username, password)
    if not user_id:
        return jsonify({"error": "User already exists"}), 409
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = db.find_user_by_username(username)
    if not user or not db.check_user_password(user, password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    token = create_token(user['_id'])
    return jsonify({"token": token})

@app.route('/api/me', methods=['GET'])
@token_required
def get_me():
    """获取当前登录用户的信息"""
    user = g.current_user
    return jsonify({"username": user['username']})


# --- 题库和进度 API ---

@app.route('/api/questions', methods=['GET'])
@token_required
def get_questions_api():
    category = request.args.get('category')
    if not category:
        return jsonify({"error": "Category is required"}), 400
        
    # 从数据库获取问题
    questions = db.get_questions(category)
    # 将 ObjectId 转换为字符串，并确保 TrueAnswer 始终为数组
    for q in questions:
        q['_id'] = str(q['_id'])
        if 'TrueAnswer' in q:
            if isinstance(q['TrueAnswer'], str):
                q['TrueAnswer'] = list(q['TrueAnswer'])
            elif not isinstance(q['TrueAnswer'], list):
                q['TrueAnswer'] = [q['TrueAnswer']]
        
        # 随机打乱选项顺序
        if 'options' in q and isinstance(q['options'], dict):
            options_items = list(q['options'].items())
            random.shuffle(options_items)
            q['options'] = dict(options_items)

    return jsonify(questions)

@app.route('/api/progress', methods=['GET'])
@token_required
def get_progress_api():
    category = request.args.get('category')
    if not category:
        return jsonify({"error": "Category is required"}), 400
        
    try:
        progress = db.get_user_progress(g.current_user['_id'], category)
        return jsonify(progress)
    except Exception as e:
        app.logger.error(f"Error fetching progress for user {g.current_user.get('_id')}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/check-answer', methods=['POST'])
@token_required
def check_answer_api():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    question_jid = data.get('question_jid')
    user_answer_keys = sorted(data.get('user_answer', []))
    category = data.get('category')

    if not all([question_jid, category]):
        return jsonify({"error": "question_jid and category are required"}), 400

    try:
        question = db.get_question_by_jid(question_jid)
        if not question:
            return jsonify({"error": "Question not found"}), 404

        correct_answer_keys = sorted(list(question['TrueAnswer']))
        is_correct = (user_answer_keys == correct_answer_keys)
        
        # 更新用户进度
        db.update_user_progress(g.current_user['_id'], category, question_jid, is_correct)
        
        return jsonify({
            "is_correct": is_correct,
            "correct_answer": question['TrueAnswer']
        })
    except Exception as e:
        app.logger.error(f"Error checking answer for question {question_jid}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# --- 考试逻辑 API ---
@app.route('/api/exam/start', methods=['POST'])
@token_required
def start_exam():
    data = request.get_json()
    category = data.get('category')
    if not category:
        return jsonify({"error": "Category is required"}), 400
        
    total_questions = 30 # 考试题目数量
    
    try:
        all_q_ids = db.get_questions(category, projection={"J_ID": 1, "_id": 0})
        if len(all_q_ids) < total_questions:
            return jsonify({"error": f"Not enough questions in category {category}"}), 400
            
        exam_q_ids = [q['J_ID'] for q in random.sample(all_q_ids, total_questions)]
        
        exam_questions = []
        for jid in exam_q_ids:
            q = db.get_question_by_jid(jid)
            if q:
                q['_id'] = str(q['_id']) # 序列化 ObjectId
                # 确保 TrueAnswer 始终为数组
                if 'TrueAnswer' in q:
                    if isinstance(q['TrueAnswer'], str):
                        q['TrueAnswer'] = list(q['TrueAnswer'])
                    elif not isinstance(q['TrueAnswer'], list):
                        q['TrueAnswer'] = [q['TrueAnswer']]
                del q['TrueAnswer'] # 安全起见，不将答案发送给客户端
                exam_questions.append(q)

        # 在真实应用中，你会创建一个考试会话(session)存入数据库
        # 这里为了简化，直接返回题目列表
        return jsonify(exam_questions)
    except Exception as e:
        app.logger.error(f"Error starting exam for category {category}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/exam/submit', methods=['POST'])
@token_required
def submit_exam():
    data = request.get_json()
    answers = data.get('answers', {}) # 格式: {"J_ID_1": ["A"], "J_ID_2": ["B", "C"]}
    category = data.get('category')
    if not category:
        return jsonify({"error": "Category is required"}), 400

    try:
        score = 0
        results = []
        for jid, user_ans in answers.items():
            question = db.get_question_by_jid(jid)
            if question:
                correct_answer_keys = sorted(list(question['TrueAnswer']))
                is_correct = sorted(user_ans) == correct_answer_keys
                if is_correct:
                    score += 1
                
                results.append({
                    "question_jid": jid,
                    "is_correct": is_correct,
                    "user_answer": user_ans,
                    "correct_answer": question['TrueAnswer']
                })
                # 提交考试后，同样更新错题集
                db.update_user_progress(g.current_user['_id'], category, jid, is_correct)
                
        return jsonify({
            "score": score,
            "total": len(answers),
            "results": results
        })
    except Exception as e:
        app.logger.error(f"Error submitting exam for category {category}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    # 确保在运行前设置了 .env 文件
    if not os.getenv("SECRET_KEY"):
        raise Exception("SECRET_KEY not found. Please create a .env file.")
    app.run(debug=True, port=5000)