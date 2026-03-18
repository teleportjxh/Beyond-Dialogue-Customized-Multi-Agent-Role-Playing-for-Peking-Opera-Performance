"""
系统测试脚本
用于验证各个模块的功能
"""
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_prompt_extractor():
    """测试Prompt提取器"""
    logger.info("=" * 60)
    logger.info("测试 PromptExtractor")
    logger.info("=" * 60)
    
    from src.extractor.prompt_extractor import PromptExtractor
    
    extractor = PromptExtractor("generated_scripts")
    
    # 测试加载剧本数据
    script_name = "煮酒论英雄"
    logger.info(f"加载剧本: {script_name}")
    
    if not extractor.load_script_data(script_name):
        logger.error("✗ 加载剧本数据失败")
        return False
    
    logger.info("✓ 剧本数据加载成功")
    
    # 测试提取prompts
    logger.info("提取视频prompts...")
    prompts = extractor.extract_video_prompts()
    
    if not prompts:
        logger.error("✗ 未提取到任何prompt")
        return False
    
    logger.info(f"✓ 提取到 {len(prompts)} 个视频prompt")
    
    # 显示第一个prompt
    if prompts:
        first_prompt = prompts[0]
        logger.info("\n第一个prompt示例:")
        logger.info(f"Turn: {first_prompt['turn']}")
        logger.info(f"角色: {first_prompt['character']}")
        logger.info(f"Prompt: {first_prompt['prompt'][:200]}...")
    
    return True


def test_director_agent():
    """测试导演Agent"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 DirectorAgent")
    logger.info("=" * 60)
    
    try:
        # 尝试从文件读取API密钥
        with open('gemini_key.txt', 'r') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        logger.warning("未找到gemini_key.txt，跳过DirectorAgent测试")
        return True
    
    from src.evaluator.director_agent import DirectorAgent
    
    director = DirectorAgent(api_key)
    logger.info("✓ DirectorAgent初始化成功")
    
    # 注意：实际评估需要视频文件，这里只测试初始化
    logger.info("注意：完整的评估测试需要实际的视频文件")
    
    return True


def test_sora2_generator():
    """测试Sora2生成器"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 Sora2Generator")
    logger.info("=" * 60)
    
    try:
        with open('openai_key.txt', 'r') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        logger.warning("未找到openai_key.txt，跳过Sora2Generator测试")
        return True
    
    from src.generator.sora2_generator import Sora2Generator
    
    generator = Sora2Generator(api_key)
    logger.info("✓ Sora2Generator初始化成功")
    
    # 注意：实际生成需要调用API，这里只测试初始化
    logger.info("注意：完整的生成测试需要调用OpenAI API")
    
    return True


def test_pipeline():
    """测试流水线"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 IntelligentPipeline")
    logger.info("=" * 60)
    
    try:
        with open('openai_key.txt', 'r') as f:
            openai_key = f.read().strip()
        with open('gemini_key.txt', 'r') as f:
            gemini_key = f.read().strip()
    except FileNotFoundError as e:
        logger.warning(f"未找到API密钥文件，跳过Pipeline测试: {e}")
        return True
    
    from src.pipeline.intelligent_pipeline import IntelligentPipeline
    
    pipeline = IntelligentPipeline(
        openai_api_key=openai_key,
        gemini_api_key=gemini_key,
        script_folder="generated_scripts",
        output_folder="generated_videos/output",
        max_iterations=3
    )
    
    logger.info("✓ IntelligentPipeline初始化成功")
    logger.info("注意：完整的流水线测试需要运行 main.py")
    
    return True


def check_project_structure():
    """检查项目结构"""
    logger.info("\n" + "=" * 60)
    logger.info("检查项目结构")
    logger.info("=" * 60)
    
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "src/__init__.py",
        "src/extractor/__init__.py",
        "src/extractor/prompt_extractor.py",
        "src/evaluator/__init__.py",
        "src/evaluator/director_agent.py",
        "src/generator/__init__.py",
        "src/generator/sora2_generator.py",
        "src/pipeline/__init__.py",
        "src/pipeline/intelligent_pipeline.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            logger.info(f"✓ {file_path}")
        else:
            logger.error(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist


def check_script_data():
    """检查剧本数据"""
    logger.info("\n" + "=" * 60)
    logger.info("检查剧本数据")
    logger.info("=" * 60)
    
    script_folder = Path("generated_scripts")
    
    if not script_folder.exists():
        logger.warning(f"剧本文件夹不存在: {script_folder}")
        return False
    
    # 查找所有剧本
    scripts = [d for d in script_folder.iterdir() if d.is_dir()]
    
    if not scripts:
        logger.warning("未找到任何剧本数据")
        return False
    
    logger.info(f"找到 {len(scripts)} 个剧本:")
    
    for script_dir in scripts:
        script_name = script_dir.name
        logger.info(f"\n剧本: {script_name}")
        
        required_files = [
            f"{script_name}_对话历史.json",
            f"{script_name}_装扮设计.json",
            f"{script_name}_场景设定.json"
        ]
        
        for filename in required_files:
            file_path = script_dir / filename
            if file_path.exists():
                logger.info(f"  ✓ {filename}")
                
                # 尝试加载JSON
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"    JSON格式正确")
                except json.JSONDecodeError as e:
                    logger.error(f"    JSON格式错误: {e}")
            else:
                logger.error(f"  ✗ {filename} 不存在")
    
    return True


def main():
    """运行所有测试"""
    logger.info("开始系统测试\n")
    
    tests = [
        ("项目结构检查", check_project_structure),
        ("剧本数据检查", check_script_data),
        ("PromptExtractor测试", test_prompt_extractor),
        ("DirectorAgent测试", test_director_agent),
        ("Sora2Generator测试", test_sora2_generator),
        ("Pipeline测试", test_pipeline)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"{test_name} 失败: {e}", exc_info=True)
            results.append((test_name, False))
    
    # 打印总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("\n🎉 所有测试通过！系统准备就绪。")
        logger.info("\n下一步:")
        logger.info("1. 配置API密钥 (openai_key.txt 和 gemini_key.txt)")
        logger.info("2. 准备剧本数据 (generated_scripts文件夹)")
        logger.info("3. 运行: python main.py 煮酒论英雄")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查上述错误信息。")


if __name__ == '__main__':
    main()
