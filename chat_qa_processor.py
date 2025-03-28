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
        
    def process_chat_records(self, excel_path: str, output_dir: str = 'output') -> Dict:
        """处理聊天记录并生成分析报告"""
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取Excel文件
        print("正在读取Excel文件...")
        try:
            df = pd.read_excel(excel_path)
            print(f"成功读取Excel文件，共 {len(df)} 行数据")
            print("列名:", df.columns.tolist())
            
            # 将时间列转换为日期时间类型
            time_columns = ['消息时间', '会话创建时间', '会话接入时间', '会话最后一条消息时间', '会话结束时间', 
                          '座席领取时间', '座席的初次响应时间']
            for col in time_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            print("时间列转换完成")
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            raise
        
        # 确保必要的列存在
        required_columns = ['消息来源', '聊天内容', '消息时间']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Excel文件缺少必要的列：{', '.join(missing_columns)}")
        
        # 检查数据是否为空
        if len(df) == 0:
            raise ValueError("Excel文件中没有数据")
        
        # 数据诊断
        print("正在进行数据诊断...")
        try:
            diagnostic_report = self.analyzer.generate_quality_report(df)
        except Exception as e:
            print(f"数据诊断失败: {str(e)}")
            raise
        
        # 数据清洗
        print("正在进行数据清洗...")
        try:
            df = self._clean_data(df)
            print(f"清洗后剩余 {len(df)} 行数据")
        except Exception as e:
            print(f"数据清洗失败: {str(e)}")
            raise
        
        # 处理问答对
        print("正在处理问答对...")
        try:
            qa_pairs = self._process_qa_pairs(df)
            print(f"提取出 {len(qa_pairs)} 个问答对")
        except Exception as e:
            print(f"问答对处理失败: {str(e)}")
            raise
        
        # 转换为DataFrame
        qa_df = pd.DataFrame(qa_pairs)
        
        # 保存结果
        print("正在保存结果...")
        try:
            self._save_results(qa_df, diagnostic_report, output_dir)
        except Exception as e:
            print(f"保存结果失败: {str(e)}")
            raise
        
        return {
            'qa_pairs': qa_df,
            'diagnostic_report': diagnostic_report
        }
    
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
        current_session_id = None
        
        total_rows = len(df)
        for idx, row in df.iterrows():
            if idx % 100 == 0:
                print(f"处理进度: {idx}/{total_rows}")
                
            message_source = str(row['消息来源']).strip()
            message_content = str(row['聊天内容']).strip()
            message_time = row['消息时间']
            session_id = str(row['会话ID']).strip() if '会话ID' in row else None
            
            # 检查是否需要开始新的会话
            if current_session_id is not None and session_id != current_session_id:
                current_customer = None
                current_service = None
                current_question = None
            
            # 更新当前会话ID
            current_session_id = session_id
            
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
                        '会话ID': current_session_id,
                        '标签': self.cleaner.extract_tags(current_question)
                    }
                    qa_pairs.append(qa_pair)
                    current_question = None
                current_service = message_source
        
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