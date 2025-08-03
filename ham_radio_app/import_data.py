import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI not found in .env file")

client = MongoClient(MONGO_URI)
db = client['ham_radio_quiz'] # 数据库名
questions_collection = db['questions'] # 集合（类似SQL的表）

def import_questions():
    """从JSON文件导入题库到MongoDB"""
    # 清空现有数据，防止重复导入
    questions_collection.delete_many({})
    print("Cleared existing questions collection.")

    libs_to_import = {
        'A': 'A-ClassQuestionLib.json',
        'B': 'B-ClassQuestionLib.json',
        'C': 'C-ClassQuestionLib.json',
        'Main': 'MainQuestionLib.json'
    }

    total_imported = 0
    for category, filename in libs_to_import.items():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                
                # 为每个问题添加分类字段
                for q in questions:
                    q['category'] = category

                if questions:
                    questions_collection.insert_many(questions)
                    print(f"Successfully imported {len(questions)} questions from {filename} for category {category}.")
                    total_imported += len(questions)
                else:
                    print(f"No questions found in {filename}.")

        except FileNotFoundError:
            print(f"Warning: {filename} not found. Skipping.")
        except Exception as e:
            print(f"An error occurred while importing {filename}: {e}")
    
    print(f"\nTotal questions imported: {total_imported}")
    # 创建索引以提高查询效率
    questions_collection.create_index([("J_ID", 1)])
    questions_collection.create_index([("category", 1)])
    print("Created indexes on J_ID and category.")

if __name__ == "__main__":
    import_questions()
    client.close()