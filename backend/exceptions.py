"""
自定义异常类
"""


class VideoAnalysisError(Exception):
    """视频分析相关错误的基类"""
    
    def __init__(self, message: str, user_message: str = None):
        """
        Args:
            message: 技术错误信息（用于日志）
            user_message: 用户友好的错误信息（用于前端显示）
        """
        super().__init__(message)
        self.user_message = user_message or message


class PoseDetectionError(VideoAnalysisError):
    """姿态检测失败错误"""
    
    def __init__(self, message: str = None):
        default_message = "视频中未能检测到有效的人体姿态"
        user_message = "视频分析失败：无法检测到人体姿态。请确保：\n" \
                      "1. 视频中有清晰可见的人物\n" \
                      "2. 人物没有被遮挡\n" \
                      "3. 视频光线充足\n" \
                      "4. 视频清晰度足够"
        super().__init__(message or default_message, user_message)


class KeyframeDetectionError(VideoAnalysisError):
    """关键帧检测失败错误"""
    
    def __init__(self, message: str = None):
        default_message = "关键帧检测失败"
        user_message = "视频分析失败：无法识别投篮动作的关键帧。请确保：\n" \
                      "1. 视频包含完整的投篮动作\n" \
                      "2. 投篮动作清晰可见\n" \
                      "3. 镜头角度合适（侧面或斜侧面效果最佳）\n" \
                      "4. 动作不要太快或太慢"
        super().__init__(message or default_message, user_message)


class InsufficientFramesError(VideoAnalysisError):
    """帧数不足错误"""
    
    def __init__(self, detected_frames: int = 0):
        message = f"检测到的有效帧数不足: {detected_frames}"
        user_message = f"视频分析失败：检测到的有效帧数太少（{detected_frames}帧）。请确保：\n" \
                      "1. 视频时长至少3秒\n" \
                      "2. 视频包含完整的投篮动作\n" \
                      "3. 视频质量良好"
        super().__init__(message, user_message)
