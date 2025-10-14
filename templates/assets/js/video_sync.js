/**
 * 视频同步控制器
 * 负责视频播放与数据图表的实时同步
 */

class VideoSyncController {
    constructor(videoElement, analysisData) {
        this.video = videoElement;
        this.data = analysisData;
        this.charts = {};
        this.currentFrameIndex = 0;
        
        this.init();
    }
    
    init() {
        // 监听视频播放事件
        this.video.addEventListener('timeupdate', () => this.onTimeUpdate());
        this.video.addEventListener('play', () => this.onPlay());
        this.video.addEventListener('pause', () => this.onPause());
        this.video.addEventListener('seeked', () => this.onSeeked());
        
        console.log('VideoSyncController initialized with', this.data.frames.length, 'frames');
    }
    
    onTimeUpdate() {
        const currentTime = this.video.currentTime;
        
        // 找到当前时间对应的帧
        this.currentFrameIndex = this.findFrameIndex(currentTime);
        
        // 更新图表指示器
        this.updateChartIndicators();
        
        // 更新当前数据显示
        this.updateCurrentDataDisplay();
    }
    
    onPlay() {
        console.log('Video playing');
    }
    
    onPause() {
        console.log('Video paused at', this.video.currentTime);
    }
    
    onSeeked() {
        console.log('Video seeked to', this.video.currentTime);
        this.onTimeUpdate();
    }
    
    findFrameIndex(currentTime) {
        // 二分查找最接近的帧
        let left = 0;
        let right = this.data.frames.length - 1;
        
        while (left < right) {
            const mid = Math.floor((left + right) / 2);
            if (this.data.frames[mid].timestamp < currentTime) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        
        // 返回最接近的帧索引
        if (left > 0 && Math.abs(this.data.frames[left - 1].timestamp - currentTime) < 
            Math.abs(this.data.frames[left].timestamp - currentTime)) {
            return left - 1;
        }
        
        return Math.min(left, this.data.frames.length - 1);
    }
    
    updateChartIndicators() {
        // 更新所有图表的当前时间指示器
        Object.values(this.charts).forEach(chart => {
            if (chart.options.plugins && chart.options.plugins.annotation) {
                // 更新垂直线位置
                chart.options.plugins.annotation.annotations.line1.xMin = this.currentFrameIndex;
                chart.options.plugins.annotation.annotations.line1.xMax = this.currentFrameIndex;
                chart.update('none'); // 使用 'none' 模式以提高性能
            }
        });
    }
    
    updateCurrentDataDisplay() {
        const currentFrame = this.data.frames[this.currentFrameIndex];
        
        if (!currentFrame) return;
        
        // 更新实时数据显示区域（如果存在）
        const dataDisplay = document.getElementById('current-data-display');
        if (dataDisplay && currentFrame.angles) {
            let html = '<h4>当前帧数据</h4>';
            html += `<p>帧号: ${currentFrame.frame_number} | 时间: ${currentFrame.timestamp.toFixed(2)}s</p>`;
            html += '<div class="current-angles">';
            
            for (const [angleName, angleValue] of Object.entries(currentFrame.angles)) {
                html += `<div class="data-item">
                    <span class="data-label">${this.formatAngleName(angleName)}</span>
                    <span class="data-value">${angleValue.toFixed(1)}°</span>
                </div>`;
            }
            
            html += '</div>';
            dataDisplay.innerHTML = html;
        }
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
    
    registerChart(chartId, chartInstance) {
        this.charts[chartId] = chartInstance;
    }
}
