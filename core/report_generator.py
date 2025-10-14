"""
HTML 报表生成器
使用 Jinja2 模板引擎生成分析报表
"""
import os
import json
import shutil
from datetime import datetime
from jinja2 import Template
from typing import Dict


class ReportGenerator:
    """报表生成器"""

    def __init__(self, template_path: str = None):
        """
        初始化报表生成器

        Args:
            template_path: 模板文件路径
        """
        if template_path is None:
            # 使用默认模板
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))
            template_path = os.path.join(
                project_root, "templates", "basketball_report.html")

        self.template_path = template_path
        self.template_dir = os.path.dirname(template_path)

    def generate_report(self, analysis_results: Dict, video_path: str,
                        output_dir: str, report_name: str = "basketball_analysis_report.html"):
        """
        生成 HTML 报表

        Args:
            analysis_results: 分析结果字典
            video_path: 视频文件路径
            output_dir: 输出目录
            report_name: 报表文件名
        """
        print("\n开始生成 HTML 报表...")

        # 创建输出目录结构
        os.makedirs(output_dir, exist_ok=True)
        assets_dir = os.path.join(output_dir, "assets")
        keyframes_dir = os.path.join(output_dir, "keyframes")
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(keyframes_dir, exist_ok=True)

        # 复制静态资源
        self._copy_assets(assets_dir)

        # 复制视频文件
        video_filename = os.path.basename(video_path)
        video_dest = os.path.join(output_dir, video_filename)
        if not os.path.exists(video_dest):
            shutil.copy2(video_path, video_dest)
            print("✓ 视频已复制到报表目录")

        # 复制关键帧图片
        self._copy_keyframe_images(analysis_results, keyframes_dir)

        # 准备模板数据
        template_data = self._prepare_template_data(
            analysis_results,
            video_filename
        )

        # 读取模板
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        # 渲染模板
        html_content = template.render(**template_data)

        # 保存 HTML 文件
        report_path = os.path.join(output_dir, report_name)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ HTML 报表已生成: {report_path}")
        return report_path

    def _copy_assets(self, assets_dir: str):
        """复制静态资源文件"""
        source_assets = os.path.join(self.template_dir, "assets")

        if os.path.exists(source_assets):
            # 复制 CSS
            css_src = os.path.join(source_assets, "css")
            css_dst = os.path.join(assets_dir, "css")
            if os.path.exists(css_src):
                os.makedirs(css_dst, exist_ok=True)
                for file in os.listdir(css_src):
                    shutil.copy2(
                        os.path.join(css_src, file),
                        os.path.join(css_dst, file)
                    )

            # 复制 JS
            js_src = os.path.join(source_assets, "js")
            js_dst = os.path.join(assets_dir, "js")
            if os.path.exists(js_src):
                os.makedirs(js_dst, exist_ok=True)
                for file in os.listdir(js_src):
                    shutil.copy2(
                        os.path.join(js_src, file),
                        os.path.join(js_dst, file)
                    )

            print("✓ 静态资源已复制")

    def _copy_keyframe_images(self, analysis_results: Dict, keyframes_dir: str):
        """复制关键帧图片"""
        keyframes = analysis_results.get("keyframes", {})

        for kf_name, kf_info in keyframes.items():
            if "image_path" in kf_info and os.path.exists(kf_info["image_path"]):
                dest_path = os.path.join(
                    keyframes_dir, f"keyframe_{kf_name}.jpg")
                shutil.copy2(kf_info["image_path"], dest_path)

        print(f"✓ {len(keyframes)} 张关键帧图片已复制")

    def _prepare_template_data(self, analysis_results: Dict, video_filename: str) -> Dict:
        """准备模板渲染数据"""
        # 准备分析数据 JSON（用于前端 JavaScript）
        analysis_data_json = self._prepare_analysis_json(analysis_results)

        # 角度名称映射（中文）
        angle_name_map = {
            'knee_angle': '膝关节角度',
            'hip_angle': '髋关节角度',
            'elbow_angle': '肘关节角度',
            'shoulder_angle': '肩关节角度',
            'wrist_angle': '手腕角度',
            'trunk_lean': '躯干倾斜'
        }

        # 计算视频时长
        duration = analysis_results["total_frames"] / analysis_results["fps"]

        # 获取新增的分析数据
        rhythm_analysis = analysis_results.get("rhythm_analysis", {})
        force_sequence = analysis_results.get("force_sequence", {})
        energy_transfer = analysis_results.get("energy_transfer", {})
        analysis_range = analysis_results.get("analysis_range", {})

        template_data = {
            "video_path": video_filename,
            "fps": analysis_results["fps"],
            "total_frames": analysis_results["total_frames"],
            "duration": f"{duration:.2f}",
            "keyframes": analysis_results.get("keyframes", {}),
            "angle_name_map": angle_name_map,
            "analysis_data_json": analysis_data_json,
            "rhythm_analysis": rhythm_analysis,
            "force_sequence": force_sequence,
            "energy_transfer": energy_transfer,
            "analysis_range": analysis_range,
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return template_data

    def _prepare_analysis_json(self, analysis_results: Dict) -> str:
        """准备用于前端的分析数据 JSON"""
        json_data = {
            "fps": analysis_results["fps"],
            "total_frames": len(analysis_results["frames"]),
            "frames": [],
            "keyframes": {},
            "rhythm_analysis": analysis_results.get("rhythm_analysis", {}),
            "force_sequence": analysis_results.get("force_sequence", {}),
            "energy_transfer": analysis_results.get("energy_transfer", {})
        }

        # 处理帧数据
        for frame in analysis_results["frames"]:
            frame_json = {
                "frame_number": frame["frame_number"],
                "timestamp": frame["timestamp"],
                "pose_detected": frame["pose_detected"],
                "angles": frame.get("angles", {}),
                "velocities": frame.get("velocities", {}),
                "accelerations": frame.get("accelerations", {})
            }
            json_data["frames"].append(frame_json)

        # 处理关键帧数据
        for kf_name, kf_info in analysis_results.get("keyframes", {}).items():
            json_data["keyframes"][kf_name] = {
                "index": kf_info["index"],
                "description": kf_info.get("description", ""),
                "timestamp": kf_info["frame_data"]["timestamp"],
                "angles": kf_info["frame_data"].get("angles", {})
            }

        return json.dumps(json_data, ensure_ascii=False)

    def generate_comparison_report(self, comparison_data: Dict,
                                   output_dir: str,
                                   report_name: str = "comparison_report.html"):
        """
        生成对比分析报告

        Args:
            comparison_data: 对比分析数据
            output_dir: 输出目录
            report_name: 报表文件名

        Returns:
            报表路径
        """
        print("\n开始生成对比分析报表...")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        assets_dir = os.path.join(output_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        # 复制静态资源
        self._copy_assets(assets_dir)

        # 准备对比报告的模板数据
        template_data = {
            "comparison": comparison_data,
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "comparison_json": json.dumps(comparison_data, ensure_ascii=False)
        }

        # 创建简单的对比报告 HTML
        html_content = self._generate_comparison_html(template_data)

        # 保存 HTML 文件
        report_path = os.path.join(output_dir, report_name)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ 对比分析报表已生成: {report_path}")
        return report_path

    def _generate_comparison_html(self, template_data: Dict) -> str:
        """生成对比报告的 HTML 内容 - 基于数据曲线"""
        comparison = template_data["comparison"]
        label1, label2 = comparison['labels']

        # 准备Chart.js所需的数据
        chart_data_json = self._prepare_chart_data(comparison, label1, label2)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投篮对比分析报告（数据曲线）</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 15px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; font-size: 18px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .metric-title {{ font-weight: bold; color: #2c3e50; margin-bottom: 10px; font-size: 16px; }}
        .metric-value {{ font-size: 24px; color: #3498db; margin: 5px 0; }}
        .chart-container {{ margin: 30px 0; height: 400px; position: relative; }}
        .chart-wrapper {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .recommendation {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 10px 0; border-radius: 5px; color: #155724; }}
        .similarity-score {{ font-size: 36px; color: #27ae60; font-weight: bold; text-align: center; padding: 20px; }}
        .phase-section {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 投篮对比分析报告（数据曲线对比）</h1>
        <p><strong>对比对象:</strong> {label1} vs {label2}</p>
        <p><strong>生成时间:</strong> {template_data['generation_time']}</p>
        
        <h2>📊 整体相似度评分</h2>
        <div class="similarity-score">
            {comparison.get('curve_similarity', {}).get('overall_similarity_score', 0)*100:.1f}%
        </div>
        <p style="text-align: center; color: #7f8c8d;">
            基于角度和速度曲线的整体相似度分析
        </p>
        
        <h2>⏱️ 整体指标对比</h2>
        <div class="metric-grid">
"""

        # 整体指标
        overall = comparison.get('overall_metrics', {})
        duration = overall.get('duration', {})
        if label1 in duration and label2 in duration:
            html += f"""
            <div class="metric-card">
                <div class="metric-title">投篮时长</div>
                <div class="metric-value">{label1}: {duration[label1]:.2f}秒</div>
                <div class="metric-value">{label2}: {duration[label2]:.2f}秒</div>
            </div>
"""

        # 最大速度对比
        max_vels = overall.get('max_velocities', {})
        if max_vels:
            html += """
            <div class="metric-card">
                <div class="metric-title">手腕最大速度</div>
"""
            if 'right_wrist' in max_vels:
                v1 = max_vels['right_wrist'].get(label1, 0)
                v2 = max_vels['right_wrist'].get(label2, 0)
                html += f"""
                <div class="metric-value">{label1}: {v1:.0f} px/s</div>
                <div class="metric-value">{label2}: {v2:.0f} px/s</div>
"""
            html += """
            </div>
"""

        html += """
        </div>
        
        <h2>🎯 关键帧时间对比</h2>
        <table>
            <thead>
                <tr>
                    <th>关键帧</th>
                    <th>{label1}</th>
                    <th>{label2}</th>
                    <th>时间差</th>
                </tr>
            </thead>
            <tbody>
""".replace('{label1}', label1).replace('{label2}', label2)

        # 关键帧时间表
        keyframe_timing = comparison.get('keyframes_timing', {})
        for kf_name in ['ball_lowest', 'knee_bend_max', 'hip_extension_max',
                        'release_prepare', 'release', 'follow_through']:
            if kf_name in keyframe_timing:
                kf_data = keyframe_timing[kf_name]
                t1 = kf_data[label1]['timestamp']
                t2 = kf_data[label2]['timestamp']
                diff = kf_data['time_diff']
                kf_label = kf_name.replace('_', ' ').title()
                html += f"""
                <tr>
                    <td>{kf_label}</td>
                    <td>{t1:.2f}秒</td>
                    <td>{t2:.2f}秒</td>
                    <td class="{'positive' if abs(diff) < 0.1 else 'negative'}">{diff:+.2f}秒</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
        
        <h2>📈 阶段数据曲线对比</h2>
        <p style="color: #7f8c8d;">对比各阶段的角度和速度变化曲线（已归一化到相同时间尺度）</p>
"""

        # 为每个阶段生成图表
        phase_comp = comparison.get('phase_comparison', {})
        phase_counter = 0
        for phase_name, phase_data in phase_comp.items():
            phase_label = phase_data.get('label', phase_name)
            html += f"""
        <div class="phase-section">
            <h3>📍 {phase_label}</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-title">阶段时长</div>
                    <div>{label1}: {phase_data.get('duration', {}).get(label1, 0)}帧</div>
                    <div>{label2}: {phase_data.get('duration', {}).get(label2, 0)}帧</div>
                </div>
            </div>
            
            <div class="chart-wrapper">
                <div class="chart-container">
                    <canvas id="angleChart{phase_counter}"></canvas>
                </div>
            </div>
            
            <div class="chart-wrapper">
                <div class="chart-container">
                    <canvas id="velocityChart{phase_counter}"></canvas>
                </div>
            </div>
        </div>
"""
            phase_counter += 1
            if phase_counter >= 3:  # 只显示前3个阶段
                break

        html += """
        <h2>💡 改进建议</h2>
        <div>
"""

        for rec in comparison.get('recommendations', []):
            html += f'            <div class="recommendation">{rec}</div>\n'

        html += f"""
        </div>
    </div>
    
    <script>
        const comparisonData = {chart_data_json};
        
        // 绘制图表
        Chart.defaults.font.family = "'Microsoft YaHei', Arial, sans-serif";
        Chart.defaults.font.size = 12;
        
        let phaseIndex = 0;
        for (const [phaseName, phaseData] of Object.entries(comparisonData.phases)) {{
            if (phaseIndex >= 3) break;
            
            // 角度曲线图
            const angleCtx = document.getElementById('angleChart' + phaseIndex).getContext('2d');
            new Chart(angleCtx, {{
                type: 'line',
                data: {{
                    labels: phaseData.time_points,
                    datasets: [
                        {{
                            label: '{label1} - 膝关节角度',
                            data: phaseData.angles_1.knee_angle,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            tension: 0.4
                        }},
                        {{
                            label: '{label2} - 膝关节角度',
                            data: phaseData.angles_2.knee_angle,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            tension: 0.4
                        }},
                        {{
                            label: '{label1} - 肘关节角度',
                            data: phaseData.angles_1.elbow_angle,
                            borderColor: 'rgba(255, 206, 86, 1)',
                            backgroundColor: 'rgba(255, 206, 86, 0.1)',
                            tension: 0.4
                        }},
                        {{
                            label: '{label2} - 肘关节角度',
                            data: phaseData.angles_2.elbow_angle,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)',
                            tension: 0.4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '关节角度变化对比'
                        }},
                        legend: {{
                            position: 'bottom'
                        }}
                    }},
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '归一化时间进度'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '角度 (度)'
                            }}
                        }}
                    }}
                }}
            }});
            
            // 速度曲线图
            const velCtx = document.getElementById('velocityChart' + phaseIndex).getContext('2d');
            new Chart(velCtx, {{
                type: 'line',
                data: {{
                    labels: phaseData.time_points,
                    datasets: [
                        {{
                            label: '{label1} - 手腕速度',
                            data: phaseData.velocities_1.right_wrist,
                            borderColor: 'rgba(153, 102, 255, 1)',
                            backgroundColor: 'rgba(153, 102, 255, 0.1)',
                            tension: 0.4
                        }},
                        {{
                            label: '{label2} - 手腕速度',
                            data: phaseData.velocities_2.right_wrist,
                            borderColor: 'rgba(255, 159, 64, 1)',
                            backgroundColor: 'rgba(255, 159, 64, 0.1)',
                            tension: 0.4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '关节速度变化对比'
                        }},
                        legend: {{
                            position: 'bottom'
                        }}
                    }},
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '归一化时间进度'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '速度 (px/s)'
                            }}
                        }}
                    }}
                }}
            }});
            
            phaseIndex++;
        }}
    </script>
</body>
</html>
"""
        return html

    def _prepare_chart_data(self, comparison: Dict, label1: str, label2: str) -> str:
        """准备Chart.js所需的数据"""
        chart_data = {
            'phases': {}
        }

        phase_comp = comparison.get('phase_comparison', {})
        for phase_name, phase_data in list(phase_comp.items())[:3]:  # 前3个阶段
            norm_data1 = phase_data.get('normalized_data', {}).get(label1, {})
            norm_data2 = phase_data.get('normalized_data', {}).get(label2, {})

            if not norm_data1 or not norm_data2:
                continue

            time_points = norm_data1.get('time_normalized', [])
            # 转换为百分比标签
            time_labels = [f"{int(t*100)}%" for t in time_points]

            chart_data['phases'][phase_name] = {
                'time_points': time_labels,
                'angles_1': norm_data1.get('angles', {}),
                'angles_2': norm_data2.get('angles', {}),
                'velocities_1': norm_data1.get('velocities', {}),
                'velocities_2': norm_data2.get('velocities', {})
            }

        return json.dumps(chart_data, ensure_ascii=False)

    def generate_keyframe_comparison_report(
        self,
        comparison_data: Dict,
        output_dir: str,
        report_name: str = "keyframe_comparison.html"
    ) -> str:
        """
        生成关键帧对比分析报告

        Args:
            comparison_data: 关键帧对比数据（来自KeyframeComparison.compare_two_keyframes）
            output_dir: 输出目录
            report_name: 报表文件名

        Returns:
            报表路径
        """
        print("\n开始生成关键帧对比报告...")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        assets_dir = os.path.join(output_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        # 复制静态资源
        self._copy_assets(assets_dir)

        # 准备模板数据
        template_data = self._prepare_keyframe_comparison_data(comparison_data)

        # 读取关键帧对比模板
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(
            project_root, "templates", "keyframe_comparison_report.html")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        # 渲染模板
        html_content = template.render(**template_data)

        # 保存 HTML 文件
        report_path = os.path.join(output_dir, report_name)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ 关键帧对比报告已生成: {report_path}")
        return report_path

    def _prepare_keyframe_comparison_data(self, comparison_data: Dict) -> Dict:
        """
        准备关键帧对比模板数据

        Args:
            comparison_data: 对比数据

        Returns:
            模板数据字典
        """
        from sports.basketball.keyframe_comparison import KeyframeComparison

        summary = comparison_data.get('summary', {})
        keyframes = comparison_data.get('keyframes', {})

        # 为每个关键帧添加中文描述和角度翻译
        for kf_type, kf_data in keyframes.items():
            # 使用中文关键帧名称
            kf_name_cn = KeyframeComparison.KEYFRAME_TYPE_MAP.get(
                kf_type, kf_type.replace('_', ' ').title())
            kf_data['description'] = kf_name_cn

            # 翻译角度名称为中文
            if 'angle_differences' in kf_data:
                angle_diffs_cn = {}
                for angle_name, diff_data in kf_data['angle_differences'].items():
                    angle_name_cn = KeyframeComparison.ANGLE_NAME_MAP.get(
                        angle_name, angle_name)
                    angle_diffs_cn[angle_name_cn] = diff_data
                kf_data['angle_differences_cn'] = angle_diffs_cn

        # 翻译 only_in_1 和 only_in_2 为中文
        only_in_1_cn = [KeyframeComparison.KEYFRAME_TYPE_MAP.get(kf, kf)
                        for kf in summary.get('only_in_1', [])]
        only_in_2_cn = [KeyframeComparison.KEYFRAME_TYPE_MAP.get(kf, kf)
                        for kf in summary.get('only_in_2', [])]

        # 按时间顺序排序关键帧（使用投篮1的时间戳，如果不存在则使用投篮2的）
        sorted_keyframes = []
        for kf_type, kf_data in keyframes.items():
            timestamp = None
            if kf_data.get('exists_in_1') and 'data1' in kf_data:
                timestamp = kf_data['data1'].get('timestamp', 0)
            elif kf_data.get('exists_in_2') and 'data2' in kf_data:
                timestamp = kf_data['data2'].get('timestamp', 0)
            else:
                timestamp = 0

            sorted_keyframes.append((kf_type, kf_data, timestamp))

        # 按时间戳排序
        sorted_keyframes.sort(key=lambda x: x[2])

        # 重新构建有序字典
        keyframes_sorted = {kf_type: kf_data for kf_type,
                            kf_data, _ in sorted_keyframes}

        template_data = {
            'label1': comparison_data.get('label1', '投篮A'),
            'label2': comparison_data.get('label2', '投篮B'),
            'total_keyframes_1': summary.get('total_keyframes_1', 0),
            'total_keyframes_2': summary.get('total_keyframes_2', 0),
            'common_keyframes_count': len(summary.get('common_keyframes', [])),
            'only_in_1_count': len(summary.get('only_in_1', [])),
            'only_in_2_count': len(summary.get('only_in_2', [])),
            'only_in_1': only_in_1_cn,
            'only_in_2': only_in_2_cn,
            'keyframes': keyframes_sorted,
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return template_data
