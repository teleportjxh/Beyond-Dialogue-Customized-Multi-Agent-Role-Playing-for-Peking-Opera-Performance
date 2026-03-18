"""
智能视频生成流水线运行脚本
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.intelligent_pipeline import IntelligentPipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python run_pipeline.py <剧本名称>")
        print("示例: python run_pipeline.py 煮酒论英雄")
        sys.exit(1)
    
    script_name = sys.argv[1]
    
    try:
        # 创建流水线实例
        pipeline = IntelligentPipeline(
            script_folder="generated_scripts",
            output_folder="generated_videos/output",
            max_iterations=3  # 最多迭代3次
        )
        
        # 运行流水线
        report = pipeline.run(script_name)
        
        if report.get('success', True):
            logger.info("\n流水线执行成功！")
            logger.info(f"通过率: {report['summary']['pass_rate']:.1%}")
            logger.info(f"平均迭代次数: {report['summary']['avg_iterations_per_video']:.1f}")
        else:
            logger.error(f"\n流水线执行失败: {report.get('error')}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"流水线执行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
