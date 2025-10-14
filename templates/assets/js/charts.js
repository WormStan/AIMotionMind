/**
 * 图表创建和管理
 * 使用 Chart.js 创建各种数据可视化图表
 */

class ChartsManager {
    constructor(analysisData, syncController) {
        this.data = analysisData;
        this.sync = syncController;
        this.charts = {};
    }
    
    createRealtimeChart(canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // 准备数据
        const frames = this.data.frames.map((f, i) => i);
        const angles = this.extractAngles();
        
        const datasets = [];
        const angleNames = Object.keys(angles);
        const colors = [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)'
        ];
        
        angleNames.forEach((angleName, index) => {
            datasets.push({
                label: this.formatAngleName(angleName),
                data: angles[angleName],
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length].replace('1)', '0.1)'),
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5
            });
        });
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: frames,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: '关节角度实时变化',
                        font: {
                            size: 16
                        }
                    },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                xMin: 0,
                                xMax: 0,
                                borderColor: 'rgb(255, 0, 0)',
                                borderWidth: 2,
                                label: {
                                    display: true,
                                    content: '当前位置',
                                    position: 'start'
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '帧号'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '角度 (度)'
                        },
                        suggestedMin: 0,
                        suggestedMax: 180
                    }
                }
            }
        });
        
        this.charts[canvasId] = chart;
        this.sync.registerChart(canvasId, chart);
        
        return chart;
    }
    
    createAngleChart(canvasId, angleName) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const timestamps = this.data.frames.map(f => f.timestamp.toFixed(2));
        const angleData = this.data.frames.map(f => f.angles[angleName] || 0);
        
        // 标记关键帧
        const keyframeAnnotations = this.createKeyframeAnnotations();
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: this.formatAngleName(angleName),
                    data: angleData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    title: {
                        display: true,
                        text: this.formatAngleName(angleName) + ' 变化曲线',
                        font: {
                            size: 14
                        }
                    },
                    annotation: {
                        annotations: keyframeAnnotations
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '时间 (秒)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '角度 (度)'
                        }
                    }
                }
            }
        });
        
        this.charts[canvasId] = chart;
        return chart;
    }
    
    createVelocityChart(canvasId, jointName) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const timestamps = this.data.frames.map(f => f.timestamp.toFixed(2));
        const velocityData = this.data.frames.map(f => 
            (f.velocities && f.velocities[jointName]) ? f.velocities[jointName] : 0
        );
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: this.formatJointName(jointName) + ' 速度',
                    data: velocityData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    title: {
                        display: true,
                        text: this.formatJointName(jointName) + ' 速度变化',
                        font: {
                            size: 14
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '时间 (秒)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '速度 (像素/秒)'
                        }
                    }
                }
            }
        });
        
        this.charts[canvasId] = chart;
        return chart;
    }
    
    extractAngles() {
        const angles = {};
        
        this.data.frames.forEach(frame => {
            if (frame.angles) {
                Object.keys(frame.angles).forEach(angleName => {
                    if (!angles[angleName]) {
                        angles[angleName] = [];
                    }
                    angles[angleName].push(frame.angles[angleName] || 0);
                });
            }
        });
        
        return angles;
    }
    
    createKeyframeAnnotations() {
        const annotations = {};
        
        Object.entries(this.data.keyframes).forEach(([kfName, kfData], index) => {
            const colors = ['red', 'green', 'blue', 'orange', 'purple'];
            annotations[`kf_${kfName}`] = {
                type: 'line',
                xMin: kfData.timestamp.toFixed(2),
                xMax: kfData.timestamp.toFixed(2),
                borderColor: colors[index % colors.length],
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                    display: true,
                    content: kfData.description,
                    position: 'start',
                    rotation: -90
                }
            };
        });
        
        return annotations;
    }
    
    formatAngleName(name) {
        const nameMap = {
            'knee_angle': '膝关节角度',
            'hip_angle': '髋关节角度',
            'elbow_angle': '肘关节角度',
            'shoulder_angle': '肩关节角度',
            'wrist_angle': '手腕角度',
            'trunk_lean': '躯干倾斜'
        };
        return nameMap[name] || name;
    }
    
    formatJointName(name) {
        const nameMap = {
            'right_wrist': '右手腕',
            'right_elbow': '右肘',
            'right_shoulder': '右肩',
            'right_hip': '右髋',
            'right_knee': '右膝',
            'right_ankle': '右脚踝'
        };
        return nameMap[name] || name;
    }
}
