import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import numpy as np

from data_cleaner import DataCleaner
from data_analyzer import DataAnalyzer

class ChatQAProcessor:
    def __init__(self):
        self.cleaner = DataCleaner()
        self.analyzer = DataAnalyzer()
        
    def process_chat_records(self, file_path: str) -> Dict:
        """处理聊天记录"""
        try:
            # 读取Excel文件，确保使用正确的编码
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # 检查必要的列是否存在
            required_columns = ['时间', '发送者', '接收者', '消息内容']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Excel文件缺少必要的列: {', '.join(missing_columns)}")
            
            print(f"成功读取Excel文件，共{len(df)}条记录")
            print("列名:", df.columns.tolist())
            
            # 确保时间列是datetime类型
            df['时间'] = pd.to_datetime(df['时间'])
            
            # 按时间排序
            df = df.sort_values('时间')
            
            # 初始化结果字典
            results = {
                'qa_pairs': [],
                'diagnostics': {
                    'total_messages': len(df),
                    'valid_messages': 0,
                    'invalid_messages': 0,
                    'qa_pairs_count': 0,
                    'missing_rates': {},
                    'emoji_frequency': 0,
                    'language_mix_ratio': 0,
                    'message_length_stats': {},
                    'session_patterns': {},
                    'quality_metrics': {}
                }
            }
            
            # 处理消息
            current_session = []
            last_time = None
            
            for _, row in df.iterrows():
                # 确保消息内容是字符串类型
                message = str(row['消息内容']).strip()
                if not message:
                    continue
                    
                # 清理消息
                cleaned_message = self.cleaner.clean_text(message)
                
                # 检查消息有效性
                if self.cleaner.is_valid_message(cleaned_message):
                    current_session.append({
                        'time': row['时间'],
                        'sender': str(row['发送者']).strip(),
                        'receiver': str(row['接收者']).strip(),
                        'content': cleaned_message
                    })
                    results['diagnostics']['valid_messages'] += 1
                else:
                    results['diagnostics']['invalid_messages'] += 1
                
                # 检查是否为新会话
                if last_time and self.cleaner.is_new_session(row['时间'], last_time):
                    # 处理当前会话
                    qa_pairs = self._process_qa_pairs(current_session)
                    results['qa_pairs'].extend(qa_pairs)
                    results['diagnostics']['qa_pairs_count'] += len(qa_pairs)
                    current_session = []
                
                last_time = row['时间']
            
            # 处理最后一个会话
            if current_session:
                qa_pairs = self._process_qa_pairs(current_session)
                results['qa_pairs'].extend(qa_pairs)
                results['diagnostics']['qa_pairs_count'] += len(qa_pairs)
            
            # 生成诊断报告
            self._generate_diagnostic_report(df, results['diagnostics'])
            
            return results
            
        except Exception as e:
            print(f"处理聊天记录时出错: {str(e)}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        # 按时间排序
        df = df.sort_values('消息时间')
        
        # 清理消息内容
        df['聊天内容'] = df['聊天内容'].apply(self.cleaner.clean_text)
        
        # 标准化时间格式
        df['消息时间'] = df['消息时间'].apply(self.cleaner.standardize_datetime)
        
        # 过滤无效消息
        df = df[df['聊天内容'].apply(self.cleaner.is_valid_message)]
        
        return df
    
    def _process_qa_pairs(self, df: pd.DataFrame) -> List[Dict]:
        """处理问答对"""
        qa_pairs = []
        current_customer = None
        current_service = None
        current_question = None
        last_message_time = None
        
        total_rows = len(df)
        for idx, row in df.iterrows():
            if idx % 100 == 0:
                print(f"处理进度: {idx}/{total_rows}")
                
            message_source = str(row['发送者']).strip()
            message_content = str(row['内容']).strip()
            message_time = row['时间']
            
            # 检查是否需要开始新的会话
            if last_message_time is not None:
                if self.cleaner.is_new_session(message_time, last_message_time):
                    current_customer = None
                    current_service = None
                    current_question = None
            
            # 处理客户消息
            if message_source.startswith('mImjj'):
                current_customer = message_source
                current_question = message_content
                current_service = None
            
            # 处理客服消息
            elif '(' in message_source and ')' in message_source:
                if current_question is not None:
                    qa_pair = {
                        '客户ID': current_customer,
                        '客服': message_source,
                        '问题': current_question,
                        '回答': message_content,
                        '时间': message_time,
                        '标签': self.cleaner.extract_tags(current_question)
                    }
                    qa_pairs.append(qa_pair)
                    current_question = None
                current_service = message_source
            
            last_message_time = message_time
        
        return qa_pairs
    
    def _save_results(self, qa_df: pd.DataFrame, diagnostic_report: Dict, output_dir: str):
        """保存处理结果"""
        # 保存问答对到Excel
        qa_output_path = os.path.join(output_dir, 'qa_pairs.xlsx')
        qa_df.to_excel(qa_output_path, index=False)
        
        # 将 NumPy 类型转换为 Python 原生类型
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif pd.isna(obj):
                return None
            return obj
        
        # 转换并保存诊断报告
        diagnostic_report = convert_numpy_types(diagnostic_report)
        report_output_path = os.path.join(output_dir, 'diagnostic_report.json')
        with open(report_output_path, 'w', encoding='utf-8') as f:
            json.dump(diagnostic_report, f, ensure_ascii=False, indent=2)
        
        # 保存知识库格式
        knowledge_base = []
        for _, row in qa_df.iterrows():
            entry = {
                'question': str(row['问题']),
                'answer': str(row['回答']),
                'tags': [str(tag) for tag in row['标签']] if isinstance(row['标签'], list) else [],
                'source': '客服聊天记录',
                'effective_date': f"{row['时间'].year}-{row['时间'].year + 2}"
            }
            entry = convert_numpy_types(entry)
            knowledge_base.append(entry)
        
        with open(os.path.join(output_dir, 'knowledge_base.json'), 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        
        print(f"处理完成，结果已保存至：{output_dir}")
        
        # 打印数据预览
        print("\n数据预览：")
        print(qa_df.head())
        print(f"\n总共处理了 {len(qa_df)} 个问答对")

if __name__ == "__main__":
    excel_path = 'data.xlsx'  # 修改为当前目录下的data.xlsx
    
    try:
        processor = ChatQAProcessor()
        results = processor.process_chat_records(excel_path)
        
        print("\n数据预览：")
        print(results['qa_pairs'].head())
        print(f"\n总共处理了 {len(results['qa_pairs'])} 个问答对")
        
        print("\n诊断报告：")
        print(json.dumps(results['diagnostic_report'], ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"处理过程中出现错误：{str(e)}") 