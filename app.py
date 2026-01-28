#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI多媒体推荐系统
主应用文件

专注于AI/机器学习领域的智能多媒体资源推荐系统
"""

import os
import sys
import shutil
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
from werkzeug.utils import secure_filename

# 添加backend路径到sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

# 导入核心模块
from backend.core.keyword_extractor import extract_keywords_from_folder
from backend.core.resource_searcher import search_all_resources, clean_extracted_content, clean_title
from backend.core.recommender import recommend_best_resources, save_recommended_resources
from backend.utils.file_utils import (
    count_txt_files,
    count_pdf_files,
    extract_zip,
    create_output_zip,
    sanitize_filename,
    convert_all_pdfs_to_txt,
    cleanup_user_data
)

# 配置路径
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "outputs")

# 确保目录存在
for dir_path in [UPLOAD_DIR, RESULTS_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 创建Flask应用
app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static'
)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR


def save_search_results(all_resources: dict, folder_name: str):
    """将搜索结果保存到 results/{folder_name}/ 下的子文件夹"""
    result_folder = os.path.join(RESULTS_DIR, folder_name)
    os.makedirs(result_folder, exist_ok=True)
    
    # 为每种类型创建子文件夹并保存
    for resource_type, resources in all_resources.items():
        type_folder = os.path.join(result_folder, resource_type)
        os.makedirs(type_folder, exist_ok=True)
        
        for i, res in enumerate(resources):
            if resource_type == "txt":
                # 清理标题
                cleaned_title = clean_title(res.get('title', 'resource'))
                filename = f"{i+1}_{sanitize_filename(cleaned_title)[:50]}.txt"
                filepath = os.path.join(type_folder, filename)
                content = res.get("content", "")
                # 清理内容：移除联系方式、部门信息等无关内容
                cleaned_content = clean_extracted_content(content)
                metadata = f"Source: {res.get('source', 'Unknown')}\n"
                metadata += f"URL: {res.get('url', '')}\n"
                metadata += "\n" + "="*50 + "\n\n"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(metadata + cleaned_content)
            
            elif resource_type == "video":
                # 清理标题
                cleaned_title = clean_title(res.get('title', 'video'))
                filename = f"{i+1}_{sanitize_filename(cleaned_title)[:50]}.txt"
                filepath = os.path.join(type_folder, filename)
                content = f"Title: {cleaned_title}\n"
                content += f"URL: {res.get('url', '')}\n"
                description = res.get('description', '')
                if description:
                    content += f"Description: {description}\n"
                if res.get("thumbnail"):
                    content += f"Thumbnail: {res.get('thumbnail')}\n"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            
            elif resource_type == "code":
                # 清理标题
                cleaned_title = clean_title(res.get('title', 'code'))
                filename = f"{i+1}_{sanitize_filename(cleaned_title)[:50]}.txt"
                filepath = os.path.join(type_folder, filename)
                content = f"Title: {cleaned_title}\n"
                content += f"URL: {res.get('url', '')}\n"
                content += f"Source: {res.get('source', 'Unknown')}\n"
                description = res.get('description', '')
                if description:
                    content += f"Description: {description}\n"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)


# ==================== 路由 ====================

@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


@app.route("/help")
def help():
    """帮助页面"""
    return render_template("help.html")


@app.route("/contact")
def contact_page():
    """加入我们页面"""
    return render_template("contact.html")


@app.route("/progress")
def progress():
    """研发进度页面"""
    return render_template("progress.html")


@app.route("/ai-enhance")
def ai_enhance():
    """AI增强页面"""
    return render_template("ai-enhance.html")


@app.route("/contact", methods=["POST"])
def contact():
    """处理加入我们表单提交"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # 验证必填字段
        if not all([name, email, subject, message]):
            return jsonify({"success": False, "error": "请填写所有必填字段"}), 400
        
        # 验证邮箱格式
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({"success": False, "error": "请输入有效的邮箱地址"}), 400
        
        # 发送邮件
        recipient_email = "czzx58@durham.ac.uk"
        
        # 创建邮件内容
        email_body = f"""
收到来自加入我们表单的新消息：

姓名: {name}
邮箱: {email}
主题: {subject}

消息内容:
{message}

---
此邮件由AI多媒体推荐系统加入我们表单自动发送
        """
        
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = email  # 使用用户提供的邮箱作为发件人
        msg['To'] = recipient_email
        msg['Subject'] = f"加入我们: {subject}"
        msg['Reply-To'] = email  # 设置回复地址为用户邮箱
        
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # 发送邮件（使用SMTP）
        # 注意：这里使用Gmail SMTP作为示例，实际使用时需要配置正确的SMTP服务器
        try:
            # 如果配置了SMTP，使用SMTP发送
            # 否则，这里只是模拟发送（实际生产环境需要配置SMTP）
            # 为了演示，我们直接返回成功，实际使用时需要配置SMTP服务器
            
            # 示例SMTP配置（需要根据实际情况修改）:
            # smtp_server = "smtp.gmail.com"
            # smtp_port = 587
            # smtp_user = "your-email@gmail.com"
            # smtp_password = "your-app-password"
            # 
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.login(smtp_user, smtp_password)
            # server.send_message(msg)
            # server.quit()
            
            # 暂时保存到文件（用于测试）
            contact_log_path = os.path.join(BASE_DIR, "data", "contact_logs.txt")
            os.makedirs(os.path.dirname(contact_log_path), exist_ok=True)
            with open(contact_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"时间: {json.dumps(str(__import__('datetime').datetime.now()), ensure_ascii=False)}\n")
                f.write(email_body)
                f.write(f"\n{'='*50}\n")
            
            return jsonify({
                "success": True,
                "message": "消息已成功发送！我们会尽快回复您。"
            })
            
        except Exception as e:
            print(f"发送邮件时出错: {str(e)}")
            return jsonify({
                "success": False,
                "error": "发送邮件时出现错误，请稍后重试或直接发送邮件至 czzx58@durham.ac.uk"
            }), 500
            
    except Exception as e:
        print(f"处理加入我们表单时出错: {str(e)}")
        return jsonify({
            "success": False,
            "error": "处理请求时出现错误，请稍后重试"
        }), 500


@app.route("/upload", methods=["POST"])
def upload_folder():
    """上传文件夹（通过zip文件）"""
    if 'folder' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400
    
    file = request.files['folder']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400
    
    if not file.filename.lower().endswith('.zip'):
        return jsonify({"error": "请上传zip格式的文件夹"}), 400
    
    folder_name = secure_filename(file.filename.replace('.zip', ''))
    upload_path = os.path.join(UPLOAD_DIR, folder_name)
    os.makedirs(upload_path, exist_ok=True)
    
    zip_path = os.path.join(upload_path, file.filename)
    file.save(zip_path)
    
    extract_path = os.path.join(upload_path, "extracted")
    os.makedirs(extract_path, exist_ok=True)
    
    if not extract_zip(zip_path, extract_path):
        return jsonify({"error": "解压失败"}), 400
    
    # 统计原始文件数量（转换前）
    pdf_count = count_pdf_files(extract_path)
    
    # 统计原始txt文件数量（不包括PDF转换后的txt和macOS系统文件）
    original_txt_count = 0
    for root, dirs, files in os.walk(extract_path):
        for f in files:
            # 过滤掉macOS资源分叉文件（以._开头）和其他系统隐藏文件
            if f.startswith('._') or f.startswith('.DS_Store'):
                continue
            if f.lower().endswith('.txt') and not f.lower().endswith('_pdf.txt'):
                original_txt_count += 1
    
    conversion_result = {"success_count": 0, "failed_count": 0}
    
    # 转换PDF文件为TXT
    if pdf_count > 0:
        print(f"发现目标文件，开始转换...")
        conversion_result = convert_all_pdfs_to_txt(extract_path)
        print(f"PDF转换完成: 成功 {conversion_result['success_count']} 个, 失败 {conversion_result['failed_count']} 个")
    
    # 统计有效文件数量：原始txt + 成功转换的PDF数量
    total_valid_files = original_txt_count + conversion_result.get('success_count', 0)
    if total_valid_files < 10:
        import shutil
        shutil.rmtree(upload_path, ignore_errors=True)
        return jsonify({
            "error": f"文件夹中有效的txt/pdf文件数量不足（需要至少10个，当前有{total_valid_files}个：{original_txt_count}个txt文件 + {conversion_result.get('success_count', 0)}个成功转换的PDF文件）"
        }), 400
    
    # 统计信息
    converted_txt = conversion_result.get('success_count', 0)
    
    return jsonify({
        "success": True,
        "folder_name": folder_name,
        "txt_count": total_valid_files,  # 实际可用的txt文件总数（原始txt + 转换后的txt）
        "pdf_count": pdf_count,
        "original_txt": original_txt_count,
        "converted_txt": converted_txt,
        "message": f"成功上传，包含{original_txt_count}个txt文件和{pdf_count}个pdf文件（成功转换{converted_txt}个）"
    })


def send_progress_event(progress, message, step=None, details=None):
    """发送SSE进度事件"""
    event_data = {
        "progress": progress,
        "message": message,
        "step": step,
        "details": details
    }
    return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


@app.route("/process", methods=["POST"])
def process_folder():
    """处理上传的文件夹（使用SSE流式返回进度）"""
    data = request.get_json()
    folder_name = data.get("folder_name")
    # 从请求中获取OpenAI API key（如果前端提供了）
    openai_api_key = data.get("openai_api_key")  # 前端传递的OpenAI API key
    
    if not folder_name:
        return jsonify({"error": "缺少folder_name参数"}), 400
    
    upload_path = os.path.join(UPLOAD_DIR, folder_name, "extracted")
    if not os.path.isdir(upload_path):
        return jsonify({"error": "文件夹不存在"}), 404
    
    def generate():
        try:
            # 步骤1: 开始处理
            yield send_progress_event(5, "🚀 开始处理文件...", "start", "正在初始化处理流程...")
            
            # 步骤2: 提取关键词
            yield send_progress_event(10, "📝 正在分析文档内容，提取关键词和主题...", "extract_keywords", "正在读取文档并分析内容...")
            keywords = extract_keywords_from_folder(upload_path, top_k=10)
            if not keywords:
                yield send_progress_event(0, "❌ 无法提取关键词", "error", "处理失败")
                return
            
            yield send_progress_event(25, f"✅ 关键词提取完成，共提取 {len(keywords)} 个关键词", "keywords_extracted", f"关键词: {', '.join(keywords[:5])}...")
            
            # 步骤3: 搜索资源
            yield send_progress_event(30, "🔍 开始搜索相关资源...", "search_resources", "正在搜索文本、视频和代码资源...")
            
            # 定义进度回调函数，实时发送搜索进度到前端
            progress_queue = []
            
            def progress_callback(progress_info):
                """进度回调函数，收集进度信息"""
                progress_queue.append(progress_info)
            
            # 在后台线程中执行搜索，避免阻塞SSE流
            import threading
            search_result = [None]
            search_error = [None]
            search_done = threading.Event()
            
            def search_thread():
                try:
                    result = search_all_resources(keywords, max_per_type=20, progress_callback=progress_callback)
                    search_result[0] = result
                except Exception as e:
                    search_error[0] = e
                finally:
                    search_done.set()
            
            thread = threading.Thread(target=search_thread)
            thread.daemon = True
            thread.start()
            
            # 实时发送进度信息
            while not search_done.is_set() or progress_queue:
                # 发送队列中的进度信息
                while progress_queue:
                    progress_info = progress_queue.pop(0)
                    progress_data = {
                        "type": "search_progress",
                        "progress": progress_info
                    }
                    yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
                
                # 短暂休眠
                import time
                time.sleep(0.1)
            
            # 等待搜索完成
            thread.join(timeout=300)
            
            if search_error[0]:
                raise search_error[0]
            
            all_resources = search_result[0]
            
            txt_found = len(all_resources.get("txt", []))
            video_found = len(all_resources.get("video", []))
            code_found = len(all_resources.get("code", []))
            
            yield send_progress_event(50, f"📊 资源搜索完成", "resources_found", 
                                    f"找到 {txt_found} 个文本资源, {video_found} 个视频资源, {code_found} 个代码资源")
            
            # 保存搜索结果
            yield send_progress_event(55, "💾 正在保存搜索结果...", "save_results", "正在保存到本地文件...")
            save_search_results(all_resources, folder_name)
            yield send_progress_event(60, "✅ 搜索结果已保存", "results_saved", "")
            
            # 步骤4: 推荐筛选
            yield send_progress_event(65, "🎯 开始推荐筛选...", "recommend", "正在计算相似度并筛选最佳资源...")
            # 返回更多候选资源（最多20个），让前端可以动态调整显示数量
            recommended = recommend_best_resources(
                upload_path,
                all_resources,
                top_k_per_type=20  # 返回更多候选，前端可以动态选择显示数量
            )
            
            txt_rec_count = len(recommended.get("txt", []))
            video_rec_count = len(recommended.get("video", []))
            code_rec_count = len(recommended.get("code", []))
            
            yield send_progress_event(80, f"✨ 推荐筛选完成", "recommend_done", 
                                    f"推荐了 {txt_rec_count} 个文本资源, {video_rec_count} 个视频资源, {code_rec_count} 个代码资源")
            
            # 步骤5: 保存推荐结果
            yield send_progress_event(85, "💾 正在保存推荐结果...", "save_recommended", "正在保存推荐资源...")
            output_folder = os.path.join(OUTPUT_DIR, folder_name)
            save_recommended_resources(recommended, output_folder)
            yield send_progress_event(90, "✅ 推荐结果已保存", "recommended_saved", "")
            
            # 步骤6: 准备返回数据
            yield send_progress_event(95, "📦 正在准备最终数据...", "prepare_data", "正在整理数据...")
            
            stats = {
                "keywords": len(keywords),
                "txt_found": txt_found,
                "video_found": video_found,
                "code_found": code_found,
                "txt_recommended": txt_rec_count,
                "video_recommended": video_rec_count,
                "code_recommended": code_rec_count,
            }
            
            # 准备推荐资源数据（用于前端展示）
            from backend.core.ai_summarizer import generate_resource_summary
            
            recommended_resources = {}
            for resource_type, resources in recommended.items():
                recommended_resources[resource_type] = []
                for res in resources:
                    resource_data = {
                        "title": res.get("title", "无标题"),
                        "url": res.get("url", ""),
                        "source": res.get("source", "Unknown"),
                        "similarity_score": res.get("similarity_score", 0.0),
                    }
                    
                    # 对所有资源类型使用AI生成简介
                    # 传递从请求中获取的API key（如果存在）
                    summary_result = generate_resource_summary(res, resource_type, openai_api_key=openai_api_key)
                    if summary_result and summary_result.get("summary"):
                        resource_data["summary"] = summary_result["summary"]
                        resource_data["summary_type"] = summary_result.get("summary_type", "ai_generated")
                    else:
                        # OpenAI失败且没有fallback，不显示摘要
                        resource_data["summary"] = None
                        resource_data["summary_type"] = None
                    
                    # 保留原始content用于其他用途
                    if resource_type == "txt":
                        content = res.get("content", "")
                        if content:
                            resource_data["description"] = content[:200] + "..." if len(content) > 200 else content
                    elif resource_type == "video":
                        if res.get("description"):
                            resource_data["description"] = res.get("description")
                        if res.get("thumbnail"):
                            resource_data["thumbnail"] = res.get("thumbnail")
                    elif resource_type == "code":
                        if res.get("description"):
                            resource_data["description"] = res.get("description")
                    
                    recommended_resources[resource_type].append(resource_data)
            
            # 发送最终结果
            final_data = {
                "progress": 100,
                "message": "✨ 处理完成！",
                "step": "complete",
                "success": True,
                "keywords": keywords,
                "stats": stats,
                "recommended_resources": recommended_resources
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
            
            # 清理文件（异步，不阻塞响应）
            import time
            time.sleep(0.5)
            cleanup_folder = os.path.join(UPLOAD_DIR, folder_name)
            if os.path.exists(cleanup_folder):
                try:
                    shutil.rmtree(cleanup_folder)
                except:
                    pass
            
            output_cleanup = os.path.join(OUTPUT_DIR, folder_name)
            if os.path.exists(output_cleanup):
                try:
                    shutil.rmtree(output_cleanup)
                except:
                    pass
            
            output_zip = os.path.join(OUTPUT_DIR, f"{folder_name}_recommended.zip")
            if os.path.exists(output_zip):
                try:
                    os.remove(output_zip)
                except:
                    pass
                    
        except Exception as e:
            import traceback
            error_data = {
                "progress": 0,
                "message": f"❌ 处理失败: {str(e)}",
                "step": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route("/download/<folder_name>")
def download_output(folder_name):
    """下载推荐结果的zip文件，下载后自动清理用户数据"""
    output_folder = os.path.join(OUTPUT_DIR, folder_name)
    zip_path = os.path.join(OUTPUT_DIR, f"{folder_name}_recommended.zip")
    
    if not os.path.isdir(output_folder):
        return jsonify({"error": "输出文件夹不存在"}), 404
    
    if not os.path.isfile(zip_path):
        if not create_output_zip(output_folder, zip_path):
            return jsonify({"error": "创建zip文件失败"}), 500
    
    # 发送文件
    response = send_file(
        zip_path,
        as_attachment=True,
        download_name=f"{folder_name}_recommended.zip",
        mimetype="application/zip"
    )
    
    # 下载后异步清理数据（使用Flask的after_request机制）
    # 注意：这里使用线程来延迟清理，确保文件已发送完成
    import threading
    def cleanup_after_download():
        import time
        time.sleep(2)  # 等待2秒确保文件下载开始
        cleanup_result = cleanup_user_data(folder_name, BASE_DIR)
        print(f"清理用户数据 {folder_name}: {cleanup_result['message']}")
    
    cleanup_thread = threading.Thread(target=cleanup_after_download)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    return response


@app.route("/status/<folder_name>")
def get_status(folder_name):
    """获取处理状态"""
    result_folder = os.path.join(RESULTS_DIR, folder_name)
    output_folder = os.path.join(OUTPUT_DIR, folder_name)
    
    return jsonify({
        "folder_name": folder_name,
        "has_results": os.path.isdir(result_folder),
        "has_output": os.path.isdir(output_folder),
        "ready_for_download": os.path.isdir(output_folder)
    })


@app.route("/cleanup/<folder_name>", methods=["POST"])
def cleanup_data(folder_name):
    """手动清理用户数据"""
    try:
        cleanup_result = cleanup_user_data(folder_name, BASE_DIR)
        if cleanup_result["success"]:
            return jsonify({
                "success": True,
                "message": cleanup_result["message"],
                "deleted": cleanup_result["deleted"]
            })
        else:
            return jsonify({
                "success": False,
                "message": cleanup_result["message"]
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"清理失败: {str(e)}"
        }), 500


if __name__ == "__main__":
    print("=" * 50)
    print("AI多媒体推荐系统")
    print("=" * 50)
    
    # 检查OpenAI API Key
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if openai_key:
        masked_key = openai_key[:10] + "..." + openai_key[-4:] if len(openai_key) > 14 else "***"
        print(f"✓ OpenAI API Key: {masked_key} (已设置)")
    else:
        print("⚠ 警告: 未检测到 OPENAI_API_KEY 环境变量")
        print("  提示: 如需使用AI摘要功能，请设置环境变量")
        print("  方法: export OPENAI_API_KEY='your-key-here'")
    
    print("=" * 50)
    print(f"上传目录: {UPLOAD_DIR}")
    print(f"结果目录: {RESULTS_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
