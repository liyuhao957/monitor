#!/usr/bin/env python3
import hashlib
import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
sys.path.append(str(Path(__file__).parent / "backend"))

from app.services.storage import get_last_result, _get_storage_path

def check_huawei_storage():
    task_name = "华为快应用引擎更新说明"
    
    print(f"🔍 检查任务: {task_name}")
    print("=" * 50)
    
    # 获取存储路径
    storage_path = _get_storage_path(task_name)
    print(f"📁 存储路径: {storage_path}")
    print(f"📄 文件存在: {storage_path.exists()}")
    
    if storage_path.exists():
        print(f"📏 文件大小: {storage_path.stat().st_size} 字节")
        
        # 读取内容
        content = get_last_result(task_name)
        if content:
            print(f"📖 内容长度: {len(content)} 字符")
            print(f"📝 内容前200字符:")
            print("-" * 40)
            print(content[:200])
            print("-" * 40)
            
            # 检查是否包含分段标记
            if "=== 提取规则" in content:
                print("✅ 包含多规则分段标记")
                sections = content.split("=== 提取规则")
                print(f"📊 分段数量: {len(sections)}")
                for i, section in enumerate(sections):
                    if section.strip():
                        print(f"  分段 {i}: {len(section)} 字符")
            else:
                print("❌ 不包含多规则分段标记")
        else:
            print("❌ 无法读取内容")
    else:
        print("❌ 存储文件不存在")
        
        # 检查存储目录
        storage_dir = storage_path.parent
        print(f"📁 存储目录: {storage_dir}")
        print(f"📁 目录存在: {storage_dir.exists()}")
        
        if storage_dir.exists():
            files = list(storage_dir.iterdir())
            print(f"📂 目录内文件数量: {len(files)}")
            for f in files:
                print(f"  - {f.name}")

if __name__ == "__main__":
    check_huawei_storage()
