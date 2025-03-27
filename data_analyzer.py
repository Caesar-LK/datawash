import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import Counter
import re

class DataAnalyzer:
    def __init__(self):
        self.emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emojis
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)

    def analyze_basic_stats(self, df: pd.DataFrame) -> Dict:
        """分析基础统计信息"""
        # 计算缺失率
        missing_rates = {}
        for col in df.columns:
            missing_rates[col] = float(df[col].isnull().mean())
        
        # 计算重复率
        duplicate_rate = float(len(df[df.duplicated()]) / len(df)) if len(df) > 0 else 0.0
        
        # 统计表情符号
        emoji_frequency = self._count_emoji_frequency(df)
        
        # 分析语言混合情况
        language_mix = self._analyze_language_mix(df)
        
        # 分析消息长度
        message_length_stats = self._analyze_message_length(df)
        
        stats = {
            'total_records': int(len(df)),
            'missing_rates': missing_rates,
            'duplicate_rate': duplicate_rate,
            'emoji_frequency': emoji_frequency,
            'language_mix': language_mix,
            'message_length_stats': message_length_stats
        }
        return stats

    def _count_emoji_frequency(self, df: pd.DataFrame) -> Dict[str, int]:
        """统计表情符号使用频率"""
        emoji_counts = Counter()
        for text in df['聊天内容'].dropna():
            emojis = self.emoji_pattern.findall(str(text))
            emoji_counts.update(emojis)
        return dict(emoji_counts.most_common(10))

    def _analyze_language_mix(self, df: pd.DataFrame) -> Dict[str, float]:
        """分析中英文混杂情况"""
        total_chars = 0
        chinese_chars = 0
        english_chars = 0
        
        for text in df['聊天内容'].dropna():
            text = str(text)
            total_chars += len(text)
            chinese_chars += len(re.findall(r'[\u4e00-\u9fff]', text))
            english_chars += len(re.findall(r'[a-zA-Z]', text))
        
        return {
            'chinese_ratio': chinese_chars / total_chars if total_chars > 0 else 0,
            'english_ratio': english_chars / total_chars if total_chars > 0 else 0,
            'mixed_ratio': (chinese_chars + english_chars) / total_chars if total_chars > 0 else 0
        }

    def _analyze_message_length(self, df: pd.DataFrame) -> Dict[str, float]:
        """分析消息长度统计"""
        lengths = df['聊天内容'].str.len().dropna()
        if len(lengths) == 0:
            return {
                'mean_length': 0.0,
                'median_length': 0.0,
                'max_length': 0.0,
                'min_length': 0.0,
                'std_length': 0.0
            }
            
        return {
            'mean_length': float(lengths.mean()),
            'median_length': float(lengths.median()),
            'max_length': float(lengths.max()),
            'min_length': float(lengths.min()),
            'std_length': float(lengths.std())
        }

    def analyze_response_time(self, df: pd.DataFrame) -> Dict:
        """分析客服响应时间"""
        df = df.sort_values('消息时间')
        response_times = []
        
        for idx in range(1, len(df)):
            if df.iloc[idx-1]['消息来源'].endswith('）') and not df.iloc[idx]['消息来源'].endswith('）'):
                time_diff = (df.iloc[idx]['消息时间'] - df.iloc[idx-1]['消息时间']).total_seconds() / 60
                response_times.append(time_diff)
        
        if not response_times:
            return {
                'mean_response_time': 0,
                'median_response_time': 0,
                'max_response_time': 0,
                'min_response_time': 0,
                'response_time_std': 0
            }
            
        response_times = np.array(response_times)
        return {
            'mean_response_time': float(np.mean(response_times)),
            'median_response_time': float(np.median(response_times)),
            'max_response_time': float(np.max(response_times)),
            'min_response_time': float(np.min(response_times)),
            'response_time_std': float(np.std(response_times))
        }

    def analyze_session_patterns(self, df: pd.DataFrame, timeout_minutes: int = 30) -> Dict:
        """分析会话模式"""
        df = df.sort_values('消息时间')
        sessions = []
        current_session = []
        
        for idx in range(len(df)):
            if idx == 0:
                current_session.append(df.iloc[idx])
            else:
                time_diff = (df.iloc[idx]['消息时间'] - df.iloc[idx-1]['消息时间']).total_seconds() / 60
                if time_diff > timeout_minutes:
                    if current_session:
                        sessions.append(current_session)
                    current_session = [df.iloc[idx]]
                else:
                    current_session.append(df.iloc[idx])
        
        if current_session:
            sessions.append(current_session)
        
        session_lengths = [len(session) for session in sessions]
        if not session_lengths:
            return {
                'total_sessions': 0,
                'mean_session_length': 0,
                'max_session_length': 0,
                'min_session_length': 0,
                'session_length_std': 0
            }
            
        return {
            'total_sessions': int(len(sessions)),
            'mean_session_length': float(np.mean(session_lengths)),
            'max_session_length': int(np.max(session_lengths)),
            'min_session_length': int(np.min(session_lengths)),
            'session_length_std': float(np.std(session_lengths))
        }

    def generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """生成质量评估报告"""
        report = {
            'basic_stats': self.analyze_basic_stats(df),
            'response_time': self.analyze_response_time(df),
            'session_patterns': self.analyze_session_patterns(df),
            'quality_metrics': {
                'completeness': 1 - df.isnull().mean().mean(),
                'consistency': self._calculate_consistency(df),
                'validity': self._calculate_validity(df)
            }
        }
        return report

    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """计算数据一致性"""
        # 检查时间顺序
        time_ordered = (df['消息时间'].is_monotonic_increasing)
        
        # 检查消息来源格式
        source_format_valid = df['消息来源'].apply(
            lambda x: (
                bool(re.match(r'^[A-Za-z0-9]+$', str(x))) or 
                bool(re.match(r'^.*?（\d+）$', str(x)))
            )
        ).mean()
        
        return (time_ordered + source_format_valid) / 2

    def _calculate_validity(self, df: pd.DataFrame) -> float:
        """计算数据有效性"""
        # 检查消息内容有效性
        content_valid = df['聊天内容'].apply(
            lambda x: len(str(x).strip()) >= 3 and 
                     not any(word in str(x).lower() for word in ['test', '测试'])
        ).mean()
        
        # 检查时间戳有效性
        time_valid = df['消息时间'].apply(
            lambda x: isinstance(x, datetime) and 
                     x.year >= 2020 and 
                     x.year <= datetime.now().year
        ).mean()
        
        return (content_valid + time_valid) / 2 