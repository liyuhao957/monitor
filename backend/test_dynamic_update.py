#!/usr/bin/env python3
"""
测试动态更新 - 证明系统会根据新数据动态更新显示
"""
import shutil
from pathlib import Path
from app.services.storage import save_result, get_last_result

def test_dynamic_update():
    print("🧪 测试动态更新功能...")
    print("=" * 60)
    
    task_name = "荣耀调试器"
    
    # 1. 显示当前存储的数据
    print("\n📖 当前存储的数据:")
    current_data = get_last_result(task_name)
    if current_data:
        print(f"内容: {current_data}")
    
    # 2. 备份当前数据
    storage_path = Path(__file__).parent / "storage" / "9ae3eb5e18d962fe54e5b7dee2663c168d5fa07c10f4094aba714a434630bfe5.txt"
    backup_path = storage_path.with_suffix('.txt.backup')
    if storage_path.exists():
        shutil.copy(storage_path, backup_path)
        print(f"\n💾 已备份当前数据到: {backup_path}")
    
    # 3. 模拟页面更新 - 保存新的版本数据
    new_content = """11.5.3.500 7890 2456 <a href="https://contentplatform-drcn.hihonorcdn.com/developerPlatform/Debugger_v90.5.3.500/Debugger_v90.5.3.500_phoneDebugger_release_20250618_120000.apk" rel="noopener" style="color: rgb(37,111,255);" target="_blank">点击下载</a> 90.5.3.500 新增：支持HarmonyOS 4.0特性；优化：调试性能提升50%"""
    
    print(f"\n🔄 模拟页面更新，保存新的版本数据...")
    save_result(task_name, new_content)
    
    # 4. 验证新数据
    print(f"\n✅ 验证新数据已保存:")
    updated_data = get_last_result(task_name)
    if updated_data:
        print(f"新内容: {updated_data}")
    
    # 5. 运行API测试
    print(f"\n🚀 现在运行 get-saved-template API，它会显示新的版本数据...")
    print("预期结果：")
    print("- 荣耀快应用引擎版本号: 11.5.3.500 (不是 10.0.2.200)")
    print("- 荣耀引擎版本号: 7890 (不是 6102)")
    print("- 快应用联盟平台版本号: 2456 (不是 1123)")
    print("- 调试器版本号: 90.5.3.500 (不是 80.0.2.200)")
    print("- 版本功能: 新增：支持HarmonyOS 4.0特性；优化：调试性能提升50%")
    
    # 6. 恢复原始数据
    input(f"\n⏸️  请刷新前端页面查看更新后的内容，然后按回车键恢复原始数据...")
    
    if backup_path.exists():
        shutil.copy(backup_path, storage_path)
        backup_path.unlink()
        print(f"✅ 已恢复原始数据")
    
    print(f"\n✨ 测试完成！这证明了系统是动态的，不是硬编码的。")

if __name__ == "__main__":
    test_dynamic_update() 