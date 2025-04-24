from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
from pathlib import Path
import io

app = FastAPI(title="QAlite API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，实际部署时应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建存储markdown文件的目录
QA_FILES_DIR = "qa_files"
os.makedirs(QA_FILES_DIR, exist_ok=True)


class QAPair(BaseModel):
    question: str
    answer: str
    userAnswer: Optional[str] = None


class MarkdownFile(BaseModel):
    filename: str
    content: Optional[str] = None
    qa_pairs: Optional[List[QAPair]] = None


# ===== 文件操作工具函数 =====

def get_file_path(filename: str) -> str:
    """获取文件的完整路径"""
    return os.path.join(QA_FILES_DIR, filename)


def get_all_markdown_files() -> List[str]:
    """获取所有markdown文件列表"""
    if not os.path.exists(QA_FILES_DIR):
        return []
    return [f for f in os.listdir(QA_FILES_DIR) if f.endswith('.md')]


def file_exists(filename: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(get_file_path(filename))


def read_markdown_file(filename: str) -> str:
    """读取markdown文件内容"""
    file_path = get_file_path(filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_markdown_file(filename: str, content: str) -> None:
    """写入markdown文件内容"""
    file_path = get_file_path(filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def delete_markdown_file(filename: str) -> None:
    """删除markdown文件"""
    file_path = get_file_path(filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    os.remove(file_path)


# ===== Markdown解析与生成工具函数 =====

def extract_markdown_prefix(content: str) -> str:
    """提取markdown文件中表格前的内容"""
    table_marker = "## 问答"
    parts = content.split(table_marker)

    if len(parts) > 1:
        return parts[0] + table_marker + "\n"

    return "# QA笔记\n\n## 问答\n"


def parse_markdown_to_qa_pairs(content: str) -> List[QAPair]:
    """将markdown内容解析为QA对列表"""
    qa_pairs = []
    print(f"开始解析markdown内容")

    # 查找表格部分
    table_pattern = r"\|\s*问题\s*\|\s*答案\s*(?:\|\s*用户回答\s*)?\|[\s\S]*?(?=\n\n|\n#|$)"
    table_match = re.search(table_pattern, content)

    if not table_match:
        print("未找到表格内容")
        return qa_pairs

    table_content = table_match.group(0)
    print(f"找到表格内容，长度: {len(table_content)}")

    # 使用pandas读取markdown表格
    try:
        # 将markdown表格转换为CSV格式以便pandas读取
        csv_content = io.StringIO()

        lines = table_content.split('\n')
        header_line = lines[0] if lines else ""
        has_user_answer = "用户回答" in header_line
        
        print(f"表格是否包含用户回答列: {has_user_answer}")

        for i, line in enumerate(lines):
            if i <= 1:  # 跳过表头和分隔行
                continue

            # 提取行内容并转换为CSV
            if '|' in line:
                cells = line.split('|')
                if len(cells) >= 3:
                    # 移除首尾的空单元格
                    cells = cells[1:-1] if cells[0].strip() == '' and cells[-1].strip() == '' else cells
                    question = cells[0].strip()
                    answer = cells[1].strip() if len(cells) > 1 else ""
                    user_answer = cells[2].strip() if has_user_answer and len(cells) > 2 else ""
                    
                    if has_user_answer:
                        csv_content.write(f'"{question}","{answer}","{user_answer}"\n')
                    else:
                        csv_content.write(f'"{question}","{answer}",""\n')

        csv_content.seek(0)
        if csv_content.getvalue().strip():
            column_names = ["问题", "答案", "用户回答"] if has_user_answer else ["问题", "答案", "用户回答"]
            df = pd.read_csv(csv_content, header=None, names=column_names)

            # 转换为QAPair对象
            for _, row in df.iterrows():
                question = row["问题"] if not pd.isna(row["问题"]) else ""
                answer = row["答案"] if not pd.isna(row["答案"]) else ""
                user_answer = row["用户回答"] if not pd.isna(row["用户回答"]) else ""

                # 只添加非空的行
                if question.strip() or answer.strip():
                    qa_pairs.append(QAPair(
                        question=question, 
                        answer=answer,
                        userAnswer=user_answer
                    ))
    except Exception as e:
        print(f"解析表格出错: {str(e)}")

    print(f"解析完成，QA对数量: {len(qa_pairs)}")
    return qa_pairs


def generate_markdown_from_qa_pairs(qa_pairs: List[QAPair], prefix: Optional[str] = None) -> str:
    """将QA对列表生成为markdown内容"""
    if prefix is None:
        prefix = "# QA笔记\n\n## 问答\n"

    # 判断是否有用户回答数据
    has_user_answers = any(qa.userAnswer for qa in qa_pairs)
    
    # 创建数据框
    data = {"问题": [], "答案": []}
    if has_user_answers:
        data["用户回答"] = []
        
    for qa in qa_pairs:
        data["问题"].append(qa.question)
        data["答案"].append(qa.answer)
        if has_user_answers:
            data["用户回答"].append(qa.userAnswer or "")

    df = pd.DataFrame(data)

    # 转换为markdown表格
    markdown_table = df.to_markdown(index=False)

    # 如果没有数据，创建一个空表格
    if len(qa_pairs) == 0:
        if has_user_answers:
            markdown_table = "| 问题 | 答案 | 用户回答 |\n|------|------|----------|"
        else:
            markdown_table = "| 问题 | 答案 |\n|------|------|"

    # 合并前缀和表格
    content = prefix + markdown_table

    return content


def create_empty_markdown(filename: str) -> str:
    """创建一个空的markdown文件内容"""
    title = filename.replace('.md', '')
    return f"# {title}\nQA速记笔记本\n\n## 问答\n| 问题 | 答案 |\n|------|------|\n"


# ===== 文件操作集成函数 =====

def load_qa_file(filename: str) -> Tuple[str, List[QAPair]]:
    """加载QA文件，返回内容和QA对列表"""
    content = read_markdown_file(filename)
    qa_pairs = parse_markdown_to_qa_pairs(content)
    return content, qa_pairs


def save_qa_file(filename: str, qa_pairs: List[QAPair], preserve_prefix: bool = True) -> str:
    """保存QA对到文件，可选是否保留原文件前缀"""
    prefix = None
    if preserve_prefix and file_exists(filename):
        original_content = read_markdown_file(filename)
        prefix = extract_markdown_prefix(original_content)

    content = generate_markdown_from_qa_pairs(qa_pairs, prefix)
    write_markdown_file(filename, content)
    return content


def add_qa_pair(filename: str, question: str, answer: str) -> List[QAPair]:
    """向文件添加一个新的QA对"""
    print(f"开始添加新的QA对到文件 {filename}: 问题={question}, 答案={answer}")

    if not file_exists(filename):
        print(f"文件不存在，创建新文件: {filename}")
        content = create_empty_markdown(filename)
        write_markdown_file(filename, content)
        qa_pairs = []
    else:
        print(f"文件存在，加载现有内容: {filename}")
        content, qa_pairs = load_qa_file(filename)
        print(f"当前QA对数量: {len(qa_pairs)}")

    # 添加新的QA对
    new_qa = QAPair(question=question, answer=answer)
    qa_pairs.append(new_qa)
    print(f"添加后QA对数量: {len(qa_pairs)}")

    # 保存文件
    print(f"保存更新的内容到文件: {filename}")
    save_qa_file(filename, qa_pairs)
    return qa_pairs


def delete_qa_pair(filename: str, index: int) -> List[QAPair]:
    """从文件中删除一个QA对"""
    if not file_exists(filename):
        raise HTTPException(status_code=404, detail="文件不存在")

    _, qa_pairs = load_qa_file(filename)

    if index < 0 or index >= len(qa_pairs):
        raise HTTPException(status_code=400, detail="无效的索引")

    # 删除指定QA对
    qa_pairs.pop(index)

    # 保存文件
    save_qa_file(filename, qa_pairs)
    return qa_pairs


def search_qa_pairs(query: str) -> List[Dict[str, Any]]:
    """在所有文件中搜索匹配的QA对"""
    if not query.strip():
        return []
        
    results = []
    print(f"搜索关键词: {query}")

    for filename in get_all_markdown_files():
        try:
            _, qa_pairs = load_qa_file(filename)
            
            for qa in qa_pairs:
                # 检查问题或答案中是否包含搜索词（不区分大小写）
                if (query.lower() in qa.question.lower() or 
                    query.lower() in qa.answer.lower()):
                    
                    # 添加匹配结果，包含文件名
                    results.append({
                        "filename": filename,
                        "question": qa.question,
                        "answer": qa.answer
                    })
                    print(f"在文件 {filename} 中找到匹配: Q={qa.question[:30]}...")
        except Exception as e:
            print(f"搜索文件 {filename} 时出错: {str(e)}")
            
    print(f"搜索完成，找到 {len(results)} 个结果")
    return results


# ===== API端点 =====

@app.get("/api/files", response_model=List[str])
async def get_files():
    """获取所有markdown文件列表"""
    return get_all_markdown_files()


@app.get("/api/files/{filename}", response_model=MarkdownFile)
async def get_file(filename: str):
    """获取特定markdown文件内容"""
    content, qa_pairs = load_qa_file(filename)

    return MarkdownFile(
        filename=filename,
        content=content,
        qa_pairs=qa_pairs
    )


@app.post("/api/files", response_model=MarkdownFile)
async def create_file(file: MarkdownFile):
    """创建新的markdown文件"""
    if not file.filename.endswith('.md'):
        file.filename += '.md'

    # 检查文件是否已存在
    if file_exists(file.filename):
        # 返回409状态码和详细错误信息
        raise HTTPException(
            status_code=409, 
            detail=f"文件 '{file.filename}' 已存在，请使用其他名称"
        )

    if file.qa_pairs:
        content = save_qa_file(file.filename, file.qa_pairs, preserve_prefix=False)
    else:
        content = create_empty_markdown(file.filename)
        write_markdown_file(file.filename, content)

    return MarkdownFile(
        filename=file.filename,
        content=content,
        qa_pairs=file.qa_pairs or []
    )


@app.put("/api/files/{filename}", response_model=MarkdownFile)
async def update_file(filename: str, file: MarkdownFile):
    """更新markdown文件内容"""
    if not file_exists(filename):
        raise HTTPException(status_code=404, detail="文件不存在")

    content = save_qa_file(filename, file.qa_pairs)

    return MarkdownFile(
        filename=filename,
        content=content,
        qa_pairs=file.qa_pairs
    )


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """删除markdown文件"""
    delete_markdown_file(filename)
    return {"message": "文件已删除"}


@app.get("/api/search", response_model=List[dict])
async def search_qa(query: str):
    """全局搜索问答对"""
    return search_qa_pairs(query)


@app.post("/api/files/{filename}/qa", response_model=MarkdownFile)
async def add_qa_to_file(filename: str, qa: QAPair):
    """向文件添加一个新的问答对"""
    print(f"API接收到添加QA对请求: 文件={filename}, 问题={qa.question}, 答案={qa.answer}")
    qa_pairs = add_qa_pair(filename, qa.question, qa.answer)
    content = read_markdown_file(filename)

    print(f"返回结果，QA对数量: {len(qa_pairs)}")
    return MarkdownFile(
        filename=filename,
        content=content,
        qa_pairs=qa_pairs
    )


@app.delete("/api/files/{filename}/qa/{index}", response_model=MarkdownFile)
async def delete_qa_from_file(filename: str, index: int):
    """从文件中删除一个问答对"""
    qa_pairs = delete_qa_pair(filename, index)
    content = read_markdown_file(filename)

    return MarkdownFile(
        filename=filename,
        content=content,
        qa_pairs=qa_pairs
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)