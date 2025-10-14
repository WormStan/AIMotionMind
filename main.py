"""
篮球投篮分析系统 - 主程序入口
交互式界面，支持分析和对比功能
"""
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.video_processor import VideoProcessor
from core.data_manager import DataManager
from core.report_generator import ReportGenerator
from sports.basketball.shot_analyzer import BasketballShotAnalyzer
from sports.basketball.keyframe_comparison import KeyframeComparison
from config import BASKETBALL_SHOT_CONFIG, OUTPUT_DIR


def clear_screen() -> None:
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header() -> None:
    """打印标题"""
    print("=" * 70)
    print("🏀 篮球投篮动作分析系统")
    print("=" * 70)


def get_user_choice(prompt: str, options: Optional[List[str]] = None, default: Optional[str] = None) -> str:
    """
    获取用户选择

    Args:
        prompt: 提示信息
        options: 有效选项列表（如果为None则接受任何输入）
        default: 默认值
    """
    while True:
        if default:
            user_input = input(f"{prompt} [默认: {default}]: ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()

        if not options or user_input.lower() in [opt.lower() for opt in options]:
            return user_input

        print(f"❌ 无效输入，请选择: {', '.join(options)}")


def list_available_analyses() -> List[Dict[str, Any]]:
    """列出所有可用的分析数据"""
    analyses = KeyframeComparison.list_available_analyses(
        OUTPUT_DIR, "basketball")

    if not analyses:
        return []

    print("\n📂 已保存的分析记录:")
    print("-" * 70)
    for i, analysis in enumerate(analyses[:10], 1):  # 最多显示10个
        print(f"  [{i}] {analysis['video_name']}")
        print(f"      时间: {analysis['timestamp']}")
        print(f"      路径: {analysis['folder']}")
        print()

    return analyses


def perform_keyframe_comparison() -> None:
    """执行关键帧对比分析"""
    print("\n【关键帧对比分析模式】")
    print("-" * 70)

    # 列出可用的分析
    analyses = list_available_analyses()

    if len(analyses) < 2:
        print("❌ 至少需要2个分析记录才能进行对比")
        print("   请先运行视频分析功能")
        return

    # 选择第一个分析
    print("请选择第一个投篮分析 (投篮A):")
    choice1 = get_user_choice(
        f"输入序号 (1-{min(len(analyses), 10)})",
        default="1"
    )
    try:
        idx1 = int(choice1) - 1
        if idx1 < 0 or idx1 >= len(analyses):
            print("❌ 无效序号")
            return
    except ValueError:
        print("❌ 无效输入")
        return

    # 选择第二个分析
    print("\n请选择第二个投篮分析 (投篮B):")
    choice2 = get_user_choice(
        f"输入序号 (1-{min(len(analyses), 10)})",
        default="2"
    )
    try:
        idx2 = int(choice2) - 1
        if idx2 < 0 or idx2 >= len(analyses):
            print("❌ 无效序号")
            return
    except ValueError:
        print("❌ 无效输入")
        return

    if idx1 == idx2:
        print("❌ 不能选择相同的分析记录")
        return

    # 加载数据
    print("\n正在加载分析数据...")
    data1 = KeyframeComparison.load_analysis_data(analyses[idx1]['path'])
    data2 = KeyframeComparison.load_analysis_data(analyses[idx2]['path'])

    if not data1 or not data2:
        print("❌ 数据加载失败")
        return

    label1 = analyses[idx1]['video_name']
    label2 = analyses[idx2]['video_name']
    analysis_path1 = analyses[idx1]['analysis_path']
    analysis_path2 = analyses[idx2]['analysis_path']

    print("已加载:")
    print(f"  投篮A: {label1}")
    print(f"  投篮B: {label2}")

    # 执行关键帧对比
    print("\n正在执行关键帧对比分析...")
    comparison = KeyframeComparison.compare_two_keyframes(
        data1, data2,
        analysis_path1, analysis_path2,
        label1, label2
    )

    # 显示对比摘要
    print("\n" + "=" * 70)
    summary = KeyframeComparison.generate_text_summary(comparison)
    print(summary)

    # 生成对比报告
    generate_report = get_user_choice(
        "\n是否生成关键帧对比HTML报告？(y/n)",
        options=['y', 'n', 'yes', 'no'],
        default='y'
    ).lower() in ['y', 'yes']

    if generate_report:
        print("\n正在生成关键帧对比报告...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(
            OUTPUT_DIR, "basketball", "comparison_reports", f"comparison_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)

        # 准备对比图片
        comparison = KeyframeComparison.prepare_comparison_images(
            comparison, output_dir)

        # 保存对比数据
        KeyframeComparison.save_comparison_data(comparison, output_dir)

        # 生成HTML报告
        report_gen = ReportGenerator()
        report_path = report_gen.generate_keyframe_comparison_report(
            comparison,
            output_dir,
            "keyframe_comparison.html"
        )

        print("\n" + "=" * 70)
        print("✅ 关键帧对比分析完成！")
        print("=" * 70)
        print(f"\n📄 对比报告: {report_path}")
        print(f"📊 对比数据: {os.path.join(output_dir, 'comparison_data.json')}")
        print(f"🖼️  关键帧图片: {os.path.join(output_dir, 'keyframe_images')}")
        print("=" * 70)
    else:
        print("\n✅ 关键帧对比分析完成！")


def perform_analysis() -> Optional[str]:
    """执行视频分析"""
    print("\n【视频分析模式】")
    print("-" * 70)

    # 1. 获取视频路径
    while True:
        video_path = get_user_choice("请输入视频文件路径")
        if os.path.exists(video_path):
            break
        print(f"❌ 文件不存在: {video_path}")

    # 2. 获取帧间隔
    frame_interval = get_user_choice(
        "请输入帧提取间隔（每N帧提取一次）",
        default="5"
    )
    try:
        frame_interval = int(frame_interval)
    except ValueError:
        frame_interval = 5
        print(f"使用默认间隔: {frame_interval}")

    # 3. 获取输出目录名称
    output_name = get_user_choice(
        "请输入输出目录名称（留空使用时间戳）",
        default=""
    )

    # 4. 是否生成报告
    generate_report = get_user_choice(
        "是否生成HTML报告？(y/n)",
        options=['y', 'n', 'yes', 'no'],
        default='y'
    ).lower() in ['y', 'yes']

    # 创建输出目录
    if output_name:
        output_dir = os.path.join(OUTPUT_DIR, "basketball", output_name)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(
            OUTPUT_DIR, "basketball", f"analysis_{timestamp}")

    frames_dir = os.path.join(output_dir, "frames")
    data_dir = os.path.join(output_dir, "data")
    report_dir = os.path.join(output_dir, "reports")
    keyframes_dir = os.path.join(output_dir, "keyframes")

    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(keyframes_dir, exist_ok=True)

    print("\n" + "=" * 70)
    print("📋 分析配置:")
    print(f"  📹 视频文件: {video_path}")
    print(f"  📁 输出目录: {output_dir}")
    print(f"  🔢 帧间隔: {frame_interval}")
    print(f"  📄 生成报告: {'是' if generate_report else '否'}")
    print("=" * 70)

    try:
        # 1. 视频处理
        print("\n【步骤 1/5】视频处理")
        print("-" * 70)
        video_processor = VideoProcessor(video_path)
        video_info = video_processor.get_video_info()

        print("✓ 视频信息:")
        print(f"  分辨率: {video_info['width']}x{video_info['height']}")
        print(f"  帧率: {video_info['fps']} FPS")
        print(f"  总帧数: {video_info['frame_count']}")
        print(f"  时长: {video_info['duration_formatted']}")

        # 提取帧
        frames_data = video_processor.extract_frames(
            frame_interval=frame_interval,
            output_dir=frames_dir
        )

        # 2. 姿态分析
        print("\n【步骤 2/5】姿态分析与运动学计算")
        print("-" * 70)
        analyzer = BasketballShotAnalyzer(BASKETBALL_SHOT_CONFIG)
        analysis_results = analyzer.analyze_frames(
            frames_data, video_info['fps'])

        # 保存关键帧图片
        analyzer.save_keyframe_images(
            keyframes_dir, analysis_results["keyframes"])

        # 3. 数据管理
        print("\n【步骤 3/5】数据处理与导出")
        print("-" * 70)
        data_manager = DataManager()

        # 导出 CSV
        data_manager.export_to_csv(data_dir)
        print("✓ CSV 文件已导出")

        # 导出 JSON
        json_path = os.path.join(data_dir, "analysis_data.json")
        data_manager.export_to_json(analysis_results, json_path)
        print("✓ JSON 文件已导出")

        # 显示统计信息
        summary = data_manager.get_summary_statistics()
        if summary.get("angles"):
            print("\n📊 关节角度统计:")
            for angle_name, stats in summary["angles"].items():
                print(f"  {angle_name}: "
                      f"均值 {stats['mean']:.1f}°, "
                      f"范围 {stats['min']:.1f}°-{stats['max']:.1f}°")

        # 显示新增分析结果
        print("\n📈 高级分析结果:")

        rhythm = analysis_results.get('rhythm_analysis', {})
        if rhythm:
            print(f"  ⏱️  动作总时长: {rhythm.get('total_duration', 0):.2f}秒")
            print(f"  🎯 节奏一致性: {rhythm.get('rhythm_consistency', 0):.3f}")

        force_seq = analysis_results.get('force_sequence', {})
        if force_seq and 'movement_pattern' in force_seq:
            pattern = force_seq['movement_pattern']
            print(f"  ⚡ 发力模式: {pattern.get('description', '未知')}")

        energy = analysis_results.get('energy_transfer', {})
        if energy:
            print(f"  💪 速度放大比: {energy.get('velocity_ratio', 0):.2f}x")
            print(f"  ⏱️  传递时序: {energy.get('transfer_timing', '未知')}")

        # 4. 生成报表
        if generate_report:
            print("\n【步骤 4/5】生成 HTML 报表")
            print("-" * 70)
            report_generator = ReportGenerator()
            report_path = report_generator.generate_report(
                analysis_results,
                video_path,
                report_dir,
                "basketball_analysis_report.html"
            )

        print("\n" + "=" * 70)
        print("✅ 分析完成！")
        print("=" * 70)

        if generate_report:
            print(f"\n📄 HTML 报表: {report_path}")
        print(f"📊 数据文件: {data_dir}")
        print(f"🖼️  关键帧图片: {keyframes_dir}")

        return output_dir

    except (IOError, ValueError, RuntimeError) as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main_menu() -> None:
    """主菜单"""
    while True:
        clear_screen()
        print_header()
        print("\n请选择功能:")
        print("  [1] 分析新视频")
        print("  [2] 关键帧对比分析")
        print("  [3] 查看历史记录")
        print("  [0] 退出程序")
        print()

        choice = get_user_choice("请输入选项", options=['0', '1', '2', '3'])

        if choice == '0':
            print("\n👋 再见!")
            sys.exit(0)
        elif choice == '1':
            perform_analysis()
        elif choice == '2':
            perform_keyframe_comparison()
        elif choice == '3':
            list_available_analyses()

        print("\n" + "=" * 70)
        input("按 Enter 键继续...")


def main() -> None:
    """主函数"""
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
        sys.exit(0)
    except (IOError, ValueError, RuntimeError) as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
