#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具模块
"""

import os
import re
import zipfile
import shutil
import warnings
import sys
import io
import contextlib
from werkzeug.utils import secure_filename
from typing import List

# PDF处理库
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# 抑制PDF处理库的警告
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*FontBBox.*')
warnings.filterwarnings('ignore', message='.*gray non-stroke color.*')
warnings.filterwarnings('ignore', message='.*invalid float value.*')


def count_txt_files(folder_path: str) -> int:
    """
    统计文件夹中txt和pdf文件的数量（不包括PDF转换后的txt文件）
    这个函数用于验证上传文件数量，应该统计原始文件
    排除macOS系统文件（以._开头的资源分叉文件）和其他隐藏文件
    """
    count = 0
    if not os.path.isdir(folder_path):
        return 0
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            # 过滤掉macOS资源分叉文件（以._开头）和其他系统隐藏文件
            if fname.startswith('._') or fname.startswith('.DS_Store'):
                continue
            # 只统计原始的.txt和.pdf文件，不包括PDF转换后的_pdf.txt文件
            if fname.lower().endswith(".pdf"):
                count += 1
            elif fname.lower().endswith(".txt") and not fname.lower().endswith("_pdf.txt"):
                count += 1
    return count


def count_all_txt_files_after_conversion(folder_path: str) -> int:
    """
    统计转换后所有txt文件的数量（包括原始txt和PDF转换后的txt）
    这个函数用于关键词提取等处理步骤
    排除macOS系统文件（以._开头的资源分叉文件）和其他隐藏文件
    """
    count = 0
    if not os.path.isdir(folder_path):
        return 0
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            # 过滤掉macOS资源分叉文件（以._开头）和其他系统隐藏文件
            if fname.startswith('._') or fname.startswith('.DS_Store'):
                continue
            if fname.lower().endswith(".txt"):
                count += 1
    return count


def count_pdf_files(folder_path: str) -> int:
    """
    统计文件夹中pdf文件的数量
    排除macOS系统文件（以._开头的资源分叉文件）和其他隐藏文件
    """
    count = 0
    if not os.path.isdir(folder_path):
        return 0
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            # 过滤掉macOS资源分叉文件（以._开头）和其他系统隐藏文件
            if fname.startswith('._') or fname.startswith('.DS_Store'):
                continue
            if fname.lower().endswith(".pdf"):
                count += 1
    return count


def get_txt_file_paths(folder_path: str) -> List[str]:
    """
    获取文件夹中所有txt文件的路径（不包括PDF转换后的txt）
    排除macOS系统文件（以._开头的资源分叉文件）和其他隐藏文件
    """
    paths = []
    if not os.path.isdir(folder_path):
        return paths
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            # 过滤掉macOS资源分叉文件（以._开头）和其他系统隐藏文件
            if fname.startswith('._') or fname.startswith('.DS_Store'):
                continue
            if fname.lower().endswith(".txt"):
                # 排除PDF转换后的txt文件（通常以_pdf.txt结尾）
                if not fname.lower().endswith("_pdf.txt"):
                    paths.append(os.path.join(root, fname))
    return sorted(paths)


def get_pdf_file_paths(folder_path: str) -> List[str]:
    """
    获取文件夹中所有pdf文件的路径
    排除macOS系统文件（以._开头的资源分叉文件）和其他隐藏文件
    """
    paths = []
    if not os.path.isdir(folder_path):
        return paths
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            # 过滤掉macOS资源分叉文件（以._开头）和其他系统隐藏文件
            if fname.startswith('._') or fname.startswith('.DS_Store'):
                continue
            if fname.lower().endswith(".pdf"):
                paths.append(os.path.join(root, fname))
    return sorted(paths)


def extract_zip(zip_path: str, extract_to: str) -> bool:
    """解压zip文件"""
    try:
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print(f"Error extracting zip: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename[:100]  # 限制长度
    return filename


def create_output_zip(folder_path: str, zip_path: str) -> bool:
    """将文件夹打包成zip文件"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"Error creating zip: {e}")
        return False


def cleanup_user_data(folder_name: str, base_dir: str) -> dict:
    """
    清理用户数据：删除上传文件、处理结果和输出文件
    
    Args:
        folder_name: 文件夹名称
        base_dir: 基础目录路径（包含uploads, results, outputs的父目录）
    
    Returns:
        {
            "success": bool,
            "deleted": {
                "uploads": bool,
                "results": bool,
                "outputs": bool
            },
            "message": str
        }
    """
    result = {
        "success": True,
        "deleted": {
            "uploads": False,
            "results": False,
            "outputs": False
        },
        "message": ""
    }
    
    uploads_dir = os.path.join(base_dir, "data", "uploads", folder_name)
    results_dir = os.path.join(base_dir, "data", "results", folder_name)
    outputs_dir = os.path.join(base_dir, "data", "outputs", folder_name)
    outputs_zip = os.path.join(base_dir, "data", "outputs", f"{folder_name}_recommended.zip")
    
    deleted_items = []
    
    # 删除上传文件
    if os.path.exists(uploads_dir):
        try:
            shutil.rmtree(uploads_dir, ignore_errors=True)
            result["deleted"]["uploads"] = True
            deleted_items.append("上传文件")
        except Exception as e:
            print(f"删除上传文件失败: {e}")
            result["success"] = False
    
    # 删除处理结果
    if os.path.exists(results_dir):
        try:
            shutil.rmtree(results_dir, ignore_errors=True)
            result["deleted"]["results"] = True
            deleted_items.append("处理结果")
        except Exception as e:
            print(f"删除处理结果失败: {e}")
            result["success"] = False
    
    # 删除输出文件
    if os.path.exists(outputs_dir):
        try:
            shutil.rmtree(outputs_dir, ignore_errors=True)
            result["deleted"]["outputs"] = True
            deleted_items.append("输出文件")
        except Exception as e:
            print(f"删除输出文件失败: {e}")
            result["success"] = False
    
    # 删除输出zip文件
    if os.path.exists(outputs_zip):
        try:
            os.remove(outputs_zip)
            deleted_items.append("输出zip文件")
        except Exception as e:
            print(f"删除输出zip文件失败: {e}")
    
    if deleted_items:
        result["message"] = f"已清理: {', '.join(deleted_items)}"
    else:
        result["message"] = "没有需要清理的文件"
    
    return result


def convert_pdf_to_txt(pdf_path: str, output_txt_path: str = None) -> str:
    """
    将PDF文件转换为TXT文件
    
    Args:
        pdf_path: PDF文件路径
        output_txt_path: 输出TXT文件路径，如果为None则自动生成
    
    Returns:
        转换后的TXT文件路径，失败返回None
    """
    if not os.path.isfile(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return None
    
    # 如果没有指定输出路径，自动生成
    if output_txt_path is None:
        base_name = os.path.splitext(pdf_path)[0]
        output_txt_path = f"{base_name}_pdf.txt"
    
    try:
        text_content = []
        
        # 优先使用pdfplumber（更准确）
        if PDFPLUMBER_AVAILABLE:
            try:
                # 抑制pdfplumber的警告输出
                import logging
                pdfplumber_logger = logging.getLogger('pdfplumber')
                original_level = pdfplumber_logger.level
                pdfplumber_logger.setLevel(logging.ERROR)
                
                # 临时重定向stderr来抑制警告
                with contextlib.redirect_stderr(io.StringIO()):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        with pdfplumber.open(pdf_path) as pdf:
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text_content.append(page_text)
                
                # 恢复日志级别
                pdfplumber_logger.setLevel(original_level)
            except Exception as e:
                # 不打印详细错误（避免终端输出过多），只在最后统一报告
                text_content = []
        
        # 如果pdfplumber失败或不可用，使用PyPDF2
        if not text_content and PYPDF2_AVAILABLE:
            try:
                # 抑制PyPDF2的警告输出
                with contextlib.redirect_stderr(io.StringIO()):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        with open(pdf_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            for page in pdf_reader.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text_content.append(page_text)
            except Exception as e:
                # 不打印详细错误，只在最后统一报告
                return None
        
        if not text_content:
            # 不打印每个失败的文件，只在最后统一报告
            return None
        
        # 保存为TXT文件
        full_text = "\n\n".join(text_content)
        # 检查提取的文本是否足够（至少50个字符）
        if len(full_text.strip()) < 50:
            # 文本内容太少，可能提取失败
            return None
        
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        # 只打印成功转换的文件名（不打印完整路径）
        filename = os.path.basename(pdf_path)
        print(f"PDF转换成功: {filename} -> {os.path.basename(output_txt_path)}")
        return output_txt_path
    
    except Exception as e:
        # 不打印详细错误，只在最后统一报告
        return None


def convert_all_pdfs_to_txt(folder_path: str) -> dict:
    """
    将文件夹中所有PDF文件转换为TXT文件
    
    Args:
        folder_path: 文件夹路径
    
    Returns:
        {
            "success_count": 成功转换的数量,
            "failed_count": 失败的数量,
            "converted_files": [(pdf_path, txt_path), ...]
        }
    """
    pdf_files = get_pdf_file_paths(folder_path)
    success_count = 0
    failed_count = 0
    converted_files = []
    failed_files = []
    
    for pdf_path in pdf_files:
        txt_path = convert_pdf_to_txt(pdf_path)
        if txt_path:
            success_count += 1
            converted_files.append((pdf_path, txt_path))
        else:
            failed_count += 1
            failed_files.append(os.path.basename(pdf_path))
    
    # 统一报告失败的PDF文件（如果有）
    if failed_files:
        print(f"PDF转换失败的文件（共{len(failed_files)}个，可能是文件损坏或格式不支持）:")
        for failed_file in failed_files[:5]:  # 只显示前5个
            print(f"  - {failed_file}")
        if len(failed_files) > 5:
            print(f"  ... 还有 {len(failed_files) - 5} 个文件转换失败")
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "converted_files": converted_files
    }

