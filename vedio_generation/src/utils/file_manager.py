#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理工具模块
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class FileManager:
    """文件管理器类"""
    
    @staticmethod
    def read_json(file_path: Path) -> Any:
        """
        读取JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            Any: JSON数据
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(file_path: Path, data: Any, indent: int = 2):
        """
        写入JSON文件
        
        Args:
            file_path: JSON文件路径
            data: 要写入的数据
            indent: 缩进空格数
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    
    @staticmethod
    def read_text(file_path: Path) -> str:
        """
        读取文本文件
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            str: 文件内容
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_text(file_path: Path, content: str):
        """
        写入文本文件
        
        Args:
            file_path: 文本文件路径
            content: 要写入的内容
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def copy_file(src: Path, dst: Path):
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    
    @staticmethod
    def move_file(src: Path, dst: Path):
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    
    @staticmethod
    def delete_file(file_path: Path):
        """
        删除文件
        
        Args:
            file_path: 文件路径
        """
        if file_path.exists():
            file_path.unlink()
    
    @staticmethod
    def list_files(directory: Path, pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索
            
        Returns:
            List[Path]: 文件路径列表
        """
        if not directory.exists():
            return []
        
        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))
    
    @staticmethod
    def ensure_directory(directory: Path):
        """
        确保目录存在
        
        Args:
            directory: 目录路径
        """
        directory.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小（字节）
        """
        return file_path.stat().st_size if file_path.exists() else 0
    
    @staticmethod
    def generate_timestamp_filename(base_name: str, extension: str = "") -> str:
        """
        生成带时间戳的文件名
        
        Args:
            base_name: 基础文件名
            extension: 文件扩展名
            
        Returns:
            str: 带时间戳的文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if extension and not extension.startswith('.'):
            extension = f".{extension}"
        return f"{base_name}_{timestamp}{extension}"
    
    @staticmethod
    def clean_directory(directory: Path, pattern: str = "*"):
        """
        清理目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
        """
        if not directory.exists():
            return
        
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_path.unlink()
    
    @staticmethod
    def archive_file(file_path: Path, archive_dir: Path) -> Path:
        """
        归档文件（移动到归档目录并添加时间戳）
        
        Args:
            file_path: 文件路径
            archive_dir: 归档目录
            
        Returns:
            Path: 归档后的文件路径
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成归档文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        archived_path = archive_dir / archived_name
        
        # 移动文件
        shutil.move(str(file_path), str(archived_path))
        
        return archived_path
