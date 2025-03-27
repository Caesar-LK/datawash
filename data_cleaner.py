import re
import unicodedata
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class DataCleaner:
    def __init__(self):
        # 初始化同义词表
        self.synonym_dict = {
            'APP': '应用',
            'app': '应用',
            '客服小姐姐': '客服人员',
            '退换货': '退货/换货',
            '亲': '您好',
            '亲亲': '您好'
        }
        
        # 初始化敏感词列表
        self.forbidden_words = [
            "傻逼", "他妈的", "操", "滚", "白痴", "笨蛋"
        ]
        
        # 初始化测试关键词
        self.test_keywords = [
            "test", "测试", "测试数据", "测试用例", "测试环境",
            "测试账号", "测试用户", "测试系统", "测试功能"
        ]
        
        # 初始化无效内容关键词
        self.invalid_keywords = [
            "[图片]", "[表情]", "[语音]", "[视频]", "[文件]",
            "[链接]", "[红包]", "[转账]", "[名片]", "[小程序]",
            "[公众号]", "[二维码]", "[位置]", "[收藏]", "[引用]",
            "[系统消息]", "[通知]", "[提醒]", "[广告]", "[推广]"
        ]
        
        # 初始化系统消息关键词
        self.system_keywords = [
            "系统", "通知", "提醒", "消息", "公告", "提示",
            "已读", "未读", "正在输入", "对方已撤回", "消息已撤回",
            "消息已删除", "消息已过期", "消息已失效", "消息已屏蔽"
        ]
        
        # 初始化广告关键词
        self.ad_keywords = [
            "广告", "推广", "营销", "优惠", "促销", "折扣",
            "特价", "限时", "秒杀", "抢购", "活动", "抽奖",
            "关注", "订阅", "公众号", "小程序", "二维码"
        ]
        
        # 初始化无意义内容关键词
        self.meaningless_keywords = [
            "嗯", "哦", "啊", "呀", "呢", "吧", "吗", "？",
            "。。。", "。。", "。。。", "。。", "。。。", "。。",
            "。。。", "。。", "。。。", "。。", "。。。", "。。"
        ]
        
        # 初始化表情符号
        self.emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)

    def standardize_encoding(self, text: str) -> str:
        """统一编码格式"""
        if not isinstance(text, str):
            return str(text)
            
        try:
            # 尝试解码为utf-8
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            else:
                # 确保文本是unicode
                text = str(text)
                
            # 统一Unicode格式
            text = unicodedata.normalize('NFKC', text)
            
            # 处理特殊字符
            text = text.replace('\u200b', '')  # 零宽空格
            text = text.replace('\u200c', '')  # 零宽非连接符
            text = text.replace('\u200d', '')  # 零宽连接符
            text = text.replace('\u200e', '')  # 左至右标记
            text = text.replace('\u200f', '')  # 右至左标记
            
            return text
        except UnicodeDecodeError:
            # 如果utf-8解码失败，尝试其他编码
            encodings = ['gbk', 'gb2312', 'gb18030', 'big5']
            for encoding in encodings:
                try:
                    if isinstance(text, bytes):
                        return text.decode(encoding)
                    return text
                except UnicodeDecodeError:
                    continue
            # 如果所有编码都失败，返回原始文本
            return str(text)

    def standardize_datetime(self, dt: datetime) -> datetime:
        """标准化日期时间格式"""
        if not isinstance(dt, datetime):
            return dt
        return dt.replace(microsecond=0)

    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not isinstance(text, str):
            return str(text)
        
        # 1. 统一编码
        text = self.standardize_encoding(text)
        
        # 2. 删除系统标记
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'【.*?】', '', text)
        
        # 3. 删除表情符号
        text = self.emoji_pattern.sub(r'', text)
        
        # 4. 删除URL链接
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 5. 删除电话号码
        text = re.sub(r'(?:\+?86)?1[3-9]\d{9}', '', text)
        
        # 6. 删除邮箱地址
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        # 7. 缩减重复字符
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # 8. 替换同义词
        for old, new in self.synonym_dict.items():
            text = text.replace(old, new)
        
        # 9. 脱敏处理
        text = re.sub(r'(1[3-9]\d{9})', '*******\g<1>[-4:]', text)  # 手机号
        text = re.sub(r'(\d{17}[\dXx])', 'ID_\g<1>[-4:]', text)  # 身份证号
        
        # 10. 删除无效内容
        for keyword in self.invalid_keywords:
            text = text.replace(keyword, '')
            
        # 11. 删除无意义内容
        for keyword in self.meaningless_keywords:
            text = text.replace(keyword, '')
        
        # 12. 删除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def is_valid_message(self, text: str) -> bool:
        """判断消息是否有效"""
        if not isinstance(text, str):
            return False
            
        # 1. 检查长度
        if len(text.strip()) < 3:
            return False
            
        # 2. 检查是否包含测试关键词
        if any(keyword in text.lower() for keyword in self.test_keywords):
            return False
            
        # 3. 检查是否包含敏感词
        if any(word in text for word in self.forbidden_words):
            return False
            
        # 4. 检查是否包含系统消息关键词
        if any(keyword in text for keyword in self.system_keywords):
            return False
            
        # 5. 检查是否包含广告关键词
        if any(keyword in text for keyword in self.ad_keywords):
            return False
            
        # 6. 检查是否只包含表情符号
        if self.emoji_pattern.match(text):
            return False
            
        # 7. 检查是否只包含URL
        if re.match(r'^https?://\S+$', text):
            return False
            
        # 8. 检查是否只包含数字
        if text.strip().isdigit():
            return False
            
        # 9. 检查是否只包含标点符号
        if re.match(r'^[^\w\s]+$', text):
            return False
            
        # 10. 检查是否包含过多重复字符
        if re.search(r'(.)\1{4,}', text):
            return False
            
        return True

    def extract_tags(self, text: str) -> List[str]:
        """提取文本标签"""
        tags = []
        
        # 定义标签规则
        tag_rules = {
            '支付问题': r'支付|付款|退款|转账|余额|费用|收费|价格|金额|支付方式|支付宝|微信支付',
            '物流问题': r'快递|物流|配送|发货|收货|运输|送达|派送|包裹|快递费|运费',
            '账户问题': r'登录|注册|密码|账号|认证|实名|身份|绑定|解绑|注销|挂失|找回',
            '商品问题': r'商品|产品|价格|质量|规格|型号|品牌|库存|缺货|断货|下架|上架',
            '订单问题': r'订单|下单|取消|修改|查询|跟踪|状态|进度|确认|取消|退款|退货',
            '服务问题': r'服务|客服|售后|维修|保修|保养|安装|调试|培训|指导|咨询',
            '系统问题': r'系统|软件|程序|应用|APP|网页|网站|网络|连接|卡顿|崩溃|错误',
            '安全隐私': r'安全|隐私|保护|泄露|加密|解密|授权|权限|验证|认证|实名',
            '优惠活动': r'优惠|活动|促销|折扣|满减|券|红包|积分|会员|VIP|特权',
            '投诉建议': r'投诉|建议|反馈|意见|举报|维权|纠纷|争议|问题|不满|差评'
        }
        
        # 转换为小写以进行不区分大小写的匹配
        text = text.lower()
        
        for tag, pattern in tag_rules.items():
            if re.search(pattern, text):
                tags.append(tag)
        
        # 添加特殊标签
        if re.search(r'etc|高速公路|通行费|收费站|etc卡|etc设备', text):
            tags.append('ETC业务')
            
        if re.search(r'车牌|车辆|汽车|驾照|驾驶证|行驶证|违章|年检|保险', text):
            tags.append('车辆相关')
            
        if re.search(r'发票|票据|收据|报销|凭证|单据', text):
            tags.append('票据问题')
            
        if re.search(r'紧急|急|快|立即|马上|尽快|加急|加急处理', text):
            tags.append('紧急问题')
        
        # 去重
        return list(set(tags))

    def is_new_session(self, current_time: datetime, last_time: datetime, 
                      timeout_minutes: int = 30) -> bool:
        """判断是否为新会话"""
        if not isinstance(current_time, datetime) or not isinstance(last_time, datetime):
            return True
        time_diff = (current_time - last_time).total_seconds() / 60
        return time_diff > timeout_minutes 