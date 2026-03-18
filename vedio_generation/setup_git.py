#!/usr/bin/env python3
"""
Git自动化脚本 - 初始化仓库并推送到GitHub
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description="", use_global=False):
    """执行命令并显示输出"""
    if description:
        print(f"\n{'='*80}")
        print(f"📌 {description}")
        print(f"{'='*80}")
    
    print(f"执行命令: {cmd}\n")
    
    try:
        # 对于配置命令，不指定cwd
        cwd = None if use_global else os.getcwd()
        
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ 成功")
            return True
        else:
            print(f"❌ 失败 (返回码: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def create_gitignore():
    """创建.gitignore文件"""
    gitignore_content = """# 敏感信息
openai_key.txt
config/api_config.py
config/*.py
!config/__init__.py
!config/settings.py

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg
*.egg-info/
dist/
build/

# 日志
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 临时文件
*.tmp
.DS_Store

# 生成的文件（可选，如果想排除）
generated_videos/
results/videos/
results/reports/
results/merged/
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("✅ 已创建 .gitignore 文件")
        return True
    else:
        print("⚠️  .gitignore 已存在，跳过创建")
        return True


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 Git仓库初始化和推送脚本")
    print("="*80)
    
    # 检查当前目录
    current_dir = Path.cwd()
    print(f"\n当前目录: {current_dir}")
    
    # 步骤0：配置安全目录（处理权限问题）
    print("\n[0/7] 配置Git安全目录")
    run_command(
        f'git config --global --add safe.directory "{current_dir}"',
        "添加目录到安全列表",
        use_global=True
    )
    
    # 步骤1：检查.gitignore
    print("\n[1/7] 检查/创建 .gitignore")
    create_gitignore()
    
    # 步骤2：初始化Git仓库
    success = run_command(
        "git init",
        "初始化Git仓库"
    )
    if not success:
        print("❌ 初始化失败，请检查是否已安装Git")
        return False
    
    # 步骤3：配置Git用户信息（全局配置）
    print("\n[2/7] 配置Git用户信息")
    print("请输入GitHub用户名 (默认: teleportjxh): ", end="")
    username = input().strip() or "teleportjxh"
    
    print("请输入邮箱地址: ", end="")
    email = input().strip()
    if not email:
        email = "user@example.com"
        print(f"使用默认邮箱: {email}")
    
    run_command(
        f'git config --global user.name "{username}"',
        f"设置Git用户名: {username}",
        use_global=True
    )
    run_command(
        f'git config --global user.email "{email}"',
        f"设置Git邮箱: {email}",
        use_global=True
    )
    
    # 步骤4：添加所有文件
    success = run_command(
        "git add .",
        "添加所有文件到暂存区"
    )
    if not success:
        return False
    
    # 步骤5：首次提交
    success = run_command(
        'git commit -m "Initial commit: 智能视频生成系统 v2.1.0\n\n- 导演Agent评估机制\n- 智能迭代优化\n- 完整的Prompt提取和构建\n- 包含详细文档和测试用例"',
        "首次提交"
    )
    if not success:
        print("⚠️  提交可能失败，继续尝试连接远程仓库...")
    
    # 步骤6：添加远程仓库
    print("\n[3/7] 添加远程仓库")
    print("请输入GitHub仓库URL (默认: https://github.com/teleportjxh/jingju.git): ", end="")
    repo_url = input().strip() or "https://github.com/teleportjxh/jingju.git"
    
    run_command(
        f'git remote add origin "{repo_url}"',
        f"添加远程仓库: {repo_url}"
    )
    
    # 步骤7：重命名分支并推送
    success = run_command(
        "git branch -M main",
        "重命名分支为 main"
    )
    
    print("\n[4/7] 推送代码到GitHub")
    print("⚠️  首次推送将要求输入GitHub凭证")
    print("    - HTTPS方式: 输入用户名和Personal Access Token")
    print("    - SSH方式: 需要提前配置SSH密钥")
    print()
    
    success = run_command(
        "git push -u origin main",
        "推送代码到GitHub"
    )
    
    if success:
        print("\n" + "="*80)
        print("✅ 成功！代码已推送到GitHub")
        print("="*80)
        print(f"\n📍 仓库地址: {repo_url}")
        print(f"📍 分支: main")
        print("\n接下来可以:")
        print("1. 在GitHub仓库设置中邀请组员")
        print("2. 组员克隆仓库: git clone <仓库URL>")
        print("3. 日常开发: git add . && git commit -m '...' && git push")
        return True
    else:
        print("\n" + "="*80)
        print("⚠️  推送可能失败，请检查:")
        print("="*80)
        print("1. GitHub用户名和密码是否正确")
        print("2. 是否已生成Personal Access Token (用作密码)")
        print("3. 网络连接是否正常")
        print("4. 仓库URL是否正确")
        print("\n💡 如果使用HTTPS失败，可尝试SSH:")
        print("   git remote set-url origin git@github.com:teleportjxh/jingju.git")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消了操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)
