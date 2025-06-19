#!/usr/bin/env python3
"""
清除华为快应用引擎更新说明任务的存储文件，强制重新生成
"""
import hashlib
import sys
from pathlib import Path

# 添加backend目录到Python路径
sys.path.append(str(Path(__file__).parent / "backend"))

def clear_huawei_storage():
    """清除华为快应用引擎更新说明任务的存储文件"""
    
    # 计算任务名的SHA256哈希值
    task_name = "华为快应用引擎更新说明"
    safe_filename = hashlib.sha256(task_name.encode('utf-8')).hexdigest()
    
    # 构建存储文件路径
    storage_dir = Path(__file__).parent / "storage"
    storage_file = storage_dir / f"{safe_filename}.txt"
    
    print(f"🔍 华为快应用引擎更新说明任务存储文件路径: {storage_file}")
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
            
            # 检查当前格式
            if "=== 规则 " in current_content:
                print("📋 当前使用旧格式: === 规则 X:")
            elif "=== 提取规则 " in current_content:
                print("📋 当前使用新格式: === 提取规则 X:")
            else:
                print("📋 未检测到分段标记")
            
            # 删除存储文件
            storage_file.unlink()
            print("✅ 存储文件已删除")
            print("🎯 下次监控将使用新的存储格式（=== 提取规则 X:）")
            
        except Exception as e:
            print(f"❌ 读取或删除文件失败: {e}")
    else:
        print("⚠️  存储文件不存在")

if __name__ == "__main__":
    print("🧹 清除华为快应用引擎更新说明存储文件工具")
    print("=" * 60)
    clear_huawei_storage()
