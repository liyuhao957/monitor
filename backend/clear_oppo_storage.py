#!/usr/bin/env python3
"""
清除OPPO任务的存储文件，强制触发变化检测
"""
import hashlib
import os
from pathlib import Path

def clear_oppo_storage():
    """清除OPPO任务的存储文件"""
    
    # 计算OPPO任务名的SHA256哈希值
    task_name = "OPPO"
    safe_filename = hashlib.sha256(task_name.encode('utf-8')).hexdigest()
    
    # 构建存储文件路径
    storage_dir = Path(__file__).parent / "storage"
    storage_file = storage_dir / f"{safe_filename}.txt"
    
    print(f"🔍 OPPO任务存储文件路径: {storage_file}")
    print(f"📝 文件名哈希: {safe_filename}")
    
    # 检查文件是否存在
    if storage_file.exists():
        print(f"📄 找到存储文件，大小: {storage_file.stat().st_size} 字节")
        
        # 读取当前内容
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
            print(f"📖 当前内容长度: {len(current_content)} 字符")
            print(f"📖 内容前200字符: {current_content[:200]}")
            
            # 删除存储文件
            storage_file.unlink()
            print("✅ 存储文件已删除")
            print("🎯 下次监控将检测到变化并触发AI代码执行")
            
        except Exception as e:
            print(f"❌ 读取或删除文件失败: {e}")
    else:
        print("⚠️  存储文件不存在")
        
        # 列出storage目录下的所有文件
        if storage_dir.exists():
            print(f"\n📁 Storage目录内容:")
            for file in storage_dir.iterdir():
                if file.is_file():
                    print(f"  - {file.name} ({file.stat().st_size} 字节)")
        else:
            print("❌ Storage目录不存在")

def list_all_storage_files():
    """列出所有存储文件及其对应的任务名"""
    
    storage_dir = Path(__file__).parent / "storage"
    
    if not storage_dir.exists():
        print("❌ Storage目录不存在")
        return
    
    print(f"\n📁 所有存储文件:")
    
    # 常见任务名列表
    common_tasks = ["OPPO", "华为快应用加载器监控", "荣耀调试器", "华为快应用引擎更新说明"]
    
    for file in storage_dir.iterdir():
        if file.is_file() and file.suffix == '.txt':
            file_size = file.stat().st_size
            print(f"  📄 {file.name} ({file_size} 字节)")
            
            # 尝试匹配常见任务名
            for task_name in common_tasks:
                expected_hash = hashlib.sha256(task_name.encode('utf-8')).hexdigest()
                if file.stem == expected_hash:
                    print(f"      ↳ 对应任务: {task_name}")
                    break

if __name__ == "__main__":
    print("🧹 清除OPPO存储文件工具")
    print("=" * 50)
    
    # 先列出所有存储文件
    list_all_storage_files()
    
    print("\n" + "=" * 50)
    
    # 清除OPPO存储文件
    clear_oppo_storage()
