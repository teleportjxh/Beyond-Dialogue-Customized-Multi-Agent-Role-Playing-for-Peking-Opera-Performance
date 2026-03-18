"""
智能视频生成系统 - 统一入口
"""
import argparse
import logging
import sys
from pathlib import Path

from src.pipeline.intelligent_pipeline import IntelligentPipeline


def setup_logging(log_level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('video_pipeline.log', encoding='utf-8')
        ]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='智能视频生成系统 - 基于导演Agent的迭代生成'
    )
    
    parser.add_argument(
        'script_name',
        type=str,
        help='剧本名称（如：煮酒论英雄）'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='API密钥（如果不提供，将从config/api_config.py读取）'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='API基础URL（如果不提供，将从config/api_config.py读取）'
    )
    
    parser.add_argument(
        '--script-folder',
        type=str,
        default='generated_scripts',
        help='剧本文件夹路径（默认：generated_scripts）'
    )
    
    parser.add_argument(
        '--output-folder',
        type=str,
        default='generated_videos/output',
        help='输出文件夹路径（默认：generated_videos/output）'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=5,
        help='每个视频的最大迭代次数（默认：5）'
    )
    
    parser.add_argument(
        '--single-turn',
        type=int,
        default=None,
        help='只生成指定turn的视频（用于测试）'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别（默认：INFO）'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("智能视频生成系统启动")
    logger.info("=" * 80)
    
    # 初始化流水线（API配置将从config/api_config.py自动读取）
    logger.info("初始化流水线...")
    try:
        pipeline = IntelligentPipeline(
            api_key=args.api_key,
            base_url=args.base_url,
            script_folder=args.script_folder,
            output_folder=args.output_folder,
            max_iterations=args.max_iterations
        )
        logger.info("流水线初始化完成")
    except ValueError as e:
        logger.error(f"初始化失败: {e}")
        logger.error("请确保config/api_config.py文件存在并包含正确的API配置")
        sys.exit(1)
    
    try:
        if args.single_turn:
            # 生成单个视频
            logger.info(f"生成单个视频 - Turn {args.single_turn}")
            result = pipeline.generate_single_video(
                script_name=args.script_name,
                turn_number=args.single_turn
            )
            
            if result['success']:
                logger.info(f"\n✓ 视频生成成功！")
                logger.info(f"输出路径: {result['final_video']}")
                logger.info(f"迭代次数: {result['iterations']}")
            else:
                logger.error(f"\n✗ 视频生成失败: {result.get('error')}")
                sys.exit(1)
        else:
            # 运行完整流水线
            logger.info(f"运行完整流水线 - 剧本: {args.script_name}")
            report = pipeline.run(args.script_name)
            
            if report.get('success') is False:
                logger.error(f"\n✗ 流水线执行失败: {report.get('error')}")
                sys.exit(1)
            
            # 打印摘要
            summary = report['summary']
            logger.info("\n" + "=" * 80)
            logger.info("执行摘要")
            logger.info("=" * 80)
            logger.info(f"总视频数: {summary['total_videos']}")
            logger.info(f"通过: {summary['passed']}")
            logger.info(f"失败: {summary['failed']}")
            logger.info(f"通过率: {summary['pass_rate']:.1%}")
            logger.info(f"总迭代次数: {summary['total_iterations']}")
            logger.info(f"平均迭代次数: {summary['avg_iterations_per_video']:.2f}")
            logger.info("=" * 80)
            
    except KeyboardInterrupt:
        logger.info("\n用户中断执行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n执行过程中发生错误: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("\n系统执行完成")


if __name__ == '__main__':
    main()
