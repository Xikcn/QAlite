import uuid
import chromadb
import re
from uuid import uuid4
from fastapi import FastAPI, Request
import os
import glob
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import json

load_dotenv()

# 初始化 FastMCP
mcp = FastMCP('qa_md_store')

# Chroma持久化目录
CHROMA_DB_DIR = "./chroma_db"
# 全局Chroma Client和Collection
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name=r"D:\Models_Home\Huggingface\hub\models--BAAI--bge-base-zh\snapshots\0e5f83d4895db7955e4cb9ed37ab73f7ded339b6")
qa_collection = chroma_client.get_or_create_collection("qa_collection", embedding_function=embedding_function)


# 1. 解析md表格
def parse_md_qa_table(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    """
    解析markdown中的QA表格，转为Qn:... An:... </end>格式
    """
    lines = md_text.splitlines()
    qa_section = False
    qa_rows = []
    for idx, line in enumerate(lines):
        if re.match(r"^##\s*问答", line):
            qa_section = True
            continue
        if qa_section:
            # 表头和分隔符跳过
            if re.match(r"^\|\s*问题", line) or re.match(r"^\|\s*:?[-]+", line):
                continue
            # 空行或下一个section结束
            if line.strip() == '' or line.startswith('#'):
                break
            # 匹配表格行
            if line.startswith('|'):
                # 去除首尾|，按|分割
                cells = [cell.strip() for cell in line.strip('|').split('|')]
                if len(cells) >= 2:
                    qa_rows.append((cells[0], cells[1]))
    # 转换为Qn/An格式
    output = []
    for i, (q, a) in enumerate(qa_rows, 1):
        q = q.replace('[换行]', '\n').replace('目前：', '').strip()
        a = a.replace('[换行]', '\n').strip()
        if q or a:

            output.append({
                'id': str(uuid4()),
                'question': q,
                'answer': a,
            })
    return output


# 2. 存入chroma
def store_qa_to_chroma(qa_pairs, md_file):
    ids = []
    documents = []
    metadatas = []
    for qa in qa_pairs:
        ids.append(qa['id'])
        documents.append(qa['question'] + '\n' + qa['answer'])
        metadatas.append({'question': qa['question'], 'answer': qa['answer'], 'md_file': md_file})


        # qa_collection.upsert(
        #     ids=[qa['id']],
        #     documents=qa['question'] + '\n' + qa['answer'],
        #     embeddings=embeddings,
        #     metadatas=[{'question': qa['question'], 'answer': qa['answer'], 'md_file': md_file}]
        # )
    qa_collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embedding_function(documents),
        metadatas=metadatas
    )

# 预览修改QA内容的函数
def preview_modify_qa(qa_id, new_question=None, new_answer=None):
    result = qa_collection.get(ids=[qa_id], include=["metadatas"])
    if not result or not result["ids"]:
        return None
    old_question = result["metadatas"][0]["question"]
    old_answer = result["metadatas"][0]["answer"]
    return {
        "old_question": old_question,
        "old_answer": old_answer,
        "new_question": new_question if new_question else old_question,
        "new_answer": new_answer if new_answer else old_answer,
    }


# 更新QA的函数
def update_qa(qa_id, new_question=None, new_answer=None):
    result = qa_collection.get(ids=[qa_id], include=["metadatas"])
    if not result or not result["ids"]:
        return False
    old_metadata = result["metadatas"][0]
    old_question = old_metadata["question"]
    old_answer = old_metadata["answer"]
    md_file = old_metadata.get("md_file")
    updated_question = new_question if new_question else old_question
    updated_answer = new_answer if new_answer else old_answer
    question = safe_text(updated_question)
    answer = safe_text(updated_answer)
    qa_collection.update(
        ids=[qa_id],
        documents=[question + '\n' + answer],
        metadatas=[{**old_metadata, "question": question, "answer": answer}]
    )
    return True


# 更新MD文件中的QA
def update_md_file(md_path, old_question, old_answer, new_question, new_answer):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    old_row_pattern = f"\\|\\s*{re.escape(old_question)}\\s*\\|\\s*{re.escape(old_answer)}\\s*\\|"
    new_row = f"| {new_question} | {new_answer} |"
    updated_content = re.sub(old_row_pattern, new_row, content)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)


# 获取已经导入Chroma的MD文件列表
def get_imported_md_files():
    results = qa_collection.get(include=["metadatas"])
    md_files = set()
    for metadata in results["metadatas"]:
        if "md_file" in metadata:
            md_files.add(metadata["md_file"])
    return list(md_files)


def safe_text(text):
    return text.replace('\n', '[换行]')


@mcp.tool()
async def import_md_to_chroma(md_path: str) -> str:
    """
    解析指定md文件并将所有问答对存入Chroma数据库
    Args:
        md_path: 需要导入的Markdown文件路径
    Returns:
        导入结果的提示信息
    """
    md_file  = os.path.splitext(md_path)[0].lower()
    md_file = os.path.basename(md_file)
    if not os.path.exists(md_path):
        return f"文件 {md_file} 不存在。"

    qa_pairs = parse_md_qa_table(md_path)
    if not qa_pairs:
        return f"{md_file} 未找到问答对，未导入。"

    store_qa_to_chroma(qa_pairs, md_file)
    return f"{md_file} 已成功导入Chroma，共导入{len(qa_pairs)}条问答。"


@mcp.tool()
async def list_imported_md_files() -> str:
    """
    获取已导入Chroma的md文件名列表
    Args:
        无
    Returns:
        已导入的Markdown文件名列表（以换行分隔的字符串）
    """
    imported_files = get_imported_md_files()
    if not imported_files:
        return "目前没有导入Chroma的MD文件。"
    return "\n".join(imported_files)


@mcp.tool()
async def rag_qa(query: str, md_file: str = None, top_k: int = 3) -> str:
    """
    用向量相似度检索返回最相关的问答，可选限定md文件，返回id方便后续操作
    Args:
        query: 需要在本地数据库查询的相关内容
        md_file: 需要在本地数据库查询的文档名称（可选）
        top_k: 需要多少条相关内容的数量，默认是1条，最大是10条
    Returns:
        搜索本地数据库的结果
    """
    filename = os.path.basename(md_file)
    filename = os.path.splitext(filename)[0]
    where = {"md_file": filename} if filename else None
    results = qa_collection.query(query_embeddings=embedding_function([query]), n_results=top_k, where=where, include=["documents", "metadatas", "distances"])
    print(results)
    if not results or not results.get('ids') or len(results['ids'][0]) == 0:
        return "未检索到相关内容。"
    output = []
    for meta, qa_id in zip(results['metadatas'][0], results['ids'][0]):
        q = meta.get('question', '').replace("|", "｜").replace("[换行]", "<br>")
        a = meta.get('answer', '').replace("|", "｜").replace("[换行]", "<br>")
        output.append(json.dumps({
            "id": qa_id,
            "问题": q,
            "答案": a,
            "md_file": meta.get('md_file', '未知')
        }, ensure_ascii=False))
    return "\n".join(output)



@mcp.tool()
async def preview_modify(qa_id: str, new_question: str = None, new_answer: str = None) -> str:
    """
    预览修改某对QA内容，返回修改前后的对比信息
    Args:
        qa_id: 需要预览的问答对ID
        new_question: 新的问题内容（可选）
        new_answer: 新的答案内容（可选）
    Returns:
        修改前后的问答内容对比信息
    """
    preview = preview_modify_qa(qa_id, new_question, new_answer)
    if not preview:
        return "未找到该QA。"
    return (f"原问题：{preview['old_question']}\n"
            f"原答案：{preview['old_answer']}\n"
            f"新问题：{preview['new_question']}\n"
            f"新答案：{preview['new_answer']}\n"
            "如果你觉得可以请回复，允许这样修改；")


@mcp.tool()
async def confirm_modify(qa_id: str, new_question: str = None, new_answer: str = None) -> str:
    """
    确认并保存对某对QA的修改
    Args:
        qa_id: 需要修改的问答对ID
        new_question: 新的问题内容（可选）
        new_answer: 新的答案内容（可选）
    Returns:
        修改结果的提示信息
    """
    if update_qa(qa_id, new_question, new_answer):
        return "修改已完成。"
    else:
        return "修改失败，未找到该问答对。"



@mcp.tool()
async def delete_qa(qa_id: str) -> str:
    """
    从Chroma数据库中删除指定的QA对
    Args:
        qa_id: 需要删除的问答对ID
    Returns:
        删除结果的提示信息
    """
    result = qa_collection.get(ids=[qa_id], include=["metadatas"])

    if not result or not result["ids"]:
        return "未找到该QA对。"

    metadata = result["metadatas"][0]
    md_file = metadata.get("md_file")
    question = metadata["question"]
    answer = metadata["answer"]

    # 从Chroma删除
    qa_collection.delete(ids=[qa_id])

    # 如果有关联的md文件，提示用户需要手动更新
    if md_file:
        return f"已从Chroma删除问答对，但需要手动从 {md_file} 文件中删除以下内容：\n问题：{question}\n答案：{answer}"

    return "已成功删除问答对。"


@mcp.tool()
async def list_qa_pairs(md_file: str = None, page: int = 1, page_size: int = 10) -> str:
    """
    分页获取已存储的QA对内容，可选按md文件筛选，便于浏览全部问答内容
    Args:
        md_file: 需要筛选的md文件名（可选）
        page: 页码，从1开始，默认第1页
        page_size: 每页条数，默认10，最大100
    Returns:
        指定页的问答内容列表（JSON字符串），包含id、问题、答案、md_file
    """
    try:
        page = int(page)
        if page < 1:
            page = 1
        page_size = int(page_size)
        if page_size < 1:
            page_size = 1
        if page_size > 100:
            page_size = 100
    except Exception:
        page, page_size = 1, 10

    where = None
    if md_file:
        filename = os.path.basename(md_file)
        filename = os.path.splitext(filename)[0]
        where = {"md_file": filename}

    # 获取全部匹配的QA对
    results = qa_collection.get(where=where, include=["metadatas"])
    ids = results.get("ids", [])
    metadatas = results.get("metadatas", [])
    total = len(ids)
    start = (page - 1) * page_size
    end = start + page_size
    page_ids = ids[start:end]
    page_metas = metadatas[start:end]
    output = []
    for qa_id, meta in zip(page_ids, page_metas):
        q = meta.get('question', '').replace("|", "｜").replace("[换行]", "<br>")
        a = meta.get('answer', '').replace("|", "｜").replace("[换行]", "<br>")
        output.append({
            "id": qa_id,
            "问题": q,
            "答案": a,
            "md_file": meta.get('md_file', '未知')
        })
    return json.dumps({
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": output
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def add_qa_pair(question: str, answer: str, md_file: str = "manual") -> str:
    """
    手动添加一条问答对到数据库，可指定来源md文件名
    Args:
        question: 问题内容
        answer: 答案内容
        md_file: 关联的md文件名（可选，默认manual）
    Returns:
        添加结果的提示信息，包含新QA的id
    """
    if not question or not answer:
        return "问题和答案不能为空。"
    qa_id = str(uuid4())
    question = safe_text(question)
    answer = safe_text(answer)
    qa_collection.upsert(
        ids=[qa_id],
        documents=[question + '\n' + answer],
        embeddings=embedding_function([question + '\n' + answer]),
        metadatas=[{'question': question, 'answer': answer, 'md_file': md_file}]
    )
    return f"已添加QA，id: {qa_id}，问题：{question}，答案：{answer}，文件：{md_file}"


@mcp.tool()
async def add_qa_pairs(qa_list: list, md_file: str = "manual") -> str:
    """
    批量添加问答对到数据库，支持去重校验（同一md_file下问题和答案完全相同则视为重复）
    Args:
        qa_list: 问答对列表，每项为{"question": 问题, "answer": 答案}
        md_file: 关联的md文件名（可选，默认manual）
    Returns:
        添加结果的提示信息，包含成功和重复的数量
    """
    if not isinstance(qa_list, list) or not qa_list:
        return "qa_list参数必须为非空列表。"
    # 获取当前md_file下所有已存在的问答对
    where = {"md_file": md_file} if md_file else None
    exist = qa_collection.get(where=where, include=["metadatas"])
    exist_set = set()
    for meta in exist.get("metadatas", []):
        exist_set.add((meta.get("question", "").strip(), meta.get("answer", "").strip()))
    add_count = 0
    repeat_count = 0
    added_ids = []
    for qa in qa_list:
        q = qa.get("question", "").strip()
        a = qa.get("answer", "").strip()
        if not q or not a:
            continue
        if (q, a) in exist_set:
            repeat_count += 1
            continue
        qa_id = str(uuid4())
        question = safe_text(q)
        answer = safe_text(a)
        qa_collection.upsert(
            ids=[qa_id],
            documents=[question + '\n' + answer],
            embeddings=embedding_function([question + '\n' + answer]),
            metadatas=[{"question": question, "answer": answer, "md_file": md_file}]
        )
        exist_set.add((question, answer))
        add_count += 1
        added_ids.append(qa_id)
    return f"批量添加完成，成功添加{add_count}条，重复{repeat_count}条。新添加的id: {added_ids}"


@mcp.tool()
async def export_md_from_db(md_file: str, output_path: str = None) -> str:
    """
    导出数据库中指定md_file的所有QA数据到md文件，表格结构与原始构建时一致
    Args:
        md_file: 需要导出的md文件名（不带扩展名也可）
        output_path: 导出md文件的保存路径（可选，默认当前目录下md_file_exported.md）
    Returns:
        导出结果的提示信息，包含导出文件路径和导出条数
    """
    if not md_file:
        return "md_file参数不能为空。"
    filename = os.path.basename(md_file)
    filename = os.path.splitext(filename)[0]
    where = {"md_file": filename}
    results = qa_collection.get(where=where, include=["metadatas"])
    metadatas = results.get("metadatas", [])
    if not metadatas:
        return f"未找到md_file={filename}的问答数据。"
    # 构建markdown表格
    lines = ["# QA笔记\n","## 问答","| 问题 | 答案 |", "|:---|:---|"]
    for meta in metadatas:
        q = md_cell_safe(meta.get("question", ""))
        a = md_cell_safe(meta.get("answer", ""))
        lines.append(f"| {q} | {a} |")
    md_content = "\n".join(lines)
    if not output_path:
        output_path = f"{filename}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return f"已导出{len(metadatas)}条问答到: {output_path}"


def md_cell_safe(text):
    # 先替换自定义占位符，再替换原始换行符
    return str(text).replace('|', '｜').replace('[换行]', '<br>').replace('\n', '<br>')


# SSE服务部分
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )



if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    import argparse
    parser = argparse.ArgumentParser(description='Run QA MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=9000, help='Port to listen on')
    args = parser.parse_args()
    starlette_app = create_starlette_app(mcp_server, debug=False)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
