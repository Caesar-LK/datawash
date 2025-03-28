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
            "test", "测试", "测试数据", "测试用例", "测试环境"
        ]
        
        # 初始化语境关键词映射
        self.context_keywords = {
            '支付问题': ['支付', '付款', '退款', '转账', '余额', '费用', '收费', '价格', '金额', '支付方式', '支付宝', '微信支付'],
            '物流问题': ['快递', '物流', '配送', '发货', '收货', '运输', '送达', '派送', '包裹', '快递费', '运费'],
            '账户问题': ['登录', '注册', '密码', '账号', '认证', '实名', '身份', '绑定', '解绑', '注销', '挂失', '找回'],
            '商品问题': ['商品', '产品', '价格', '质量', '规格', '型号', '品牌', '库存', '缺货', '断货', '下架', '上架'],
            '订单问题': ['订单', '下单', '取消', '修改', '查询', '跟踪', '状态', '进度', '确认', '取消', '退款', '退货'],
            '服务问题': ['服务', '客服', '售后', '维修', '保修', '保养', '安装', '调试', '培训', '指导', '咨询'],
            '系统问题': ['系统', '软件', '程序', '应用', 'APP', '网页', '网站', '网络', '连接', '卡顿', '崩溃', '错误'],
            '安全隐私': ['安全', '隐私', '保护', '泄露', '加密', '解密', '授权', '权限', '验证', '认证', '实名'],
            '优惠活动': ['优惠', '活动', '促销', '折扣', '满减', '券', '红包', '积分', '会员', 'VIP', '特权'],
            '投诉建议': ['投诉', '建议', '反馈', '意见', '举报', '维权', '纠纷', '争议', '问题', '不满', '差评'],
            'ETC业务': ['etc', '高速公路', '通行费', '收费站', 'etc卡', 'etc设备'],
            '车辆相关': ['车牌', '车辆', '汽车', '驾照', '驾驶证', '行驶证', '违章', '年检', '保险'],
            '票据问题': ['发票', '票据', '收据', '报销', '凭证', '单据'],
            '紧急问题': ['紧急', '急', '快', '立即', '马上', '尽快', '加急', '加急处理']
        }
        
        # 初始化无效内容关键词
        self.invalid_keywords = [
            # 系统消息和标记
            "[图片]", "[表情]", "[语音]", "[视频]", "[文件]",
            "[链接]", "[红包]", "[转账]", "[位置]", "[名片]",
            "[小程序]", "[公众号]", "[群聊]", "[私聊]", "[系统]",
            "[正在输入]", "[已读]", "[已送达]", "[已发送]",
            "[撤回]", "[删除]", "[清空]", "[置顶]", "[免打扰]",
            
            # 自动回复和模板消息
            "您好，很高兴为您服务",
            "感谢您的咨询",
            "正在为您转接",
            "请稍等",
            "正在处理中",
            "正在为您查询",
            "正在为您核实",
            "正在为您处理",
            "正在为您办理",
            "正在为您审核",
            "正在为您转接相关部门",
            "正在为您联系相关工作人员",
            "正在为您协调处理",
            "正在为您跟进",
            "正在为您反馈",
            "正在为您升级处理",
            "正在为您加急处理",
            "正在为您优先处理",
            "正在为您安排专员处理",
            "正在为您安排技术人员处理",
            
            # 常见无效内容
            "收到", "好的", "嗯", "哦", "啊", "呀", "呢", "吧",
            "谢谢", "不客气", "再见", "拜拜", "晚安", "早安",
            "在吗", "在的", "在的哦", "在的呢", "在的呀",
            "请稍等", "稍等", "等等", "等一下", "稍等片刻",
            "正在输入", "正在输入中", "对方正在输入",
            "已读", "已送达", "已发送", "发送成功",
            "正在加载", "加载中", "加载失败", "加载完成",
            
            # 表情符号和特殊字符
            "😊", "😄", "😃", "😀", "😁", "😅", "😂", "🤣",
            "👍", "👎", "👌", "✌️", "🤝", "🙏", "💪",
            "❤️", "💕", "💖", "💗", "💓", "💞", "💝",
            "🌟", "⭐", "✨", "💫", "💥", "💦", "💨",
            
            # 广告和推广
            "推广", "广告", "优惠", "促销", "特价", "折扣",
            "限时", "秒杀", "抢购", "团购", "拼团", "砍价",
            "抽奖", "中奖", "奖品", "礼品", "赠品", "礼包",
            
            # 系统提示和状态
            "系统维护中", "系统升级中", "系统更新中",
            "网络连接中", "正在连接", "连接失败",
            "正在同步", "同步完成", "同步失败",
            "正在下载", "下载完成", "下载失败",
            "正在上传", "上传完成", "上传失败",
            
            # 客服协作相关
            "需要转接", "需要升级", "需要反馈",
            "需要核实", "需要确认", "需要验证",
            "需要审核", "需要审批", "需要处理",
            "需要跟进", "需要协调", "需要沟通",
            "需要联系", "需要对接", "需要交接",
            "需要转交", "需要移交", "需要转介",
            "需要转派", "需要转办", "需要转达",
            "需要转告", "需要转述", "需要转报",
            "需要转呈", "需要转递", "需要转送",
            
            # 其他无效内容
            "点击查看", "查看更多", "查看详情",
            "复制成功", "复制失败", "复制链接",
            "分享成功", "分享失败", "分享链接",
            "转发成功", "转发失败", "转发链接",
            "保存成功", "保存失败", "保存图片",
            "删除成功", "删除失败", "删除消息",
            "撤回成功", "撤回失败", "撤回消息",
            "清空成功", "清空失败", "清空聊天",
            "置顶成功", "置顶失败", "取消置顶",
            "免打扰", "消息免打扰", "群聊免打扰",
            "已静音", "已屏蔽", "已拉黑", "已举报",
            "已关注", "已取消关注", "已点赞", "已收藏",
            
            # 新增的自动回复和系统消息
            "正在为您查询相关信息",
            "正在为您核实具体情况",
            "正在为您联系相关部门",
            "正在为您协调处理方案",
            "正在为您安排专人处理",
            "正在为您升级处理级别",
            "正在为您加急处理问题",
            "正在为您优先处理请求",
            "正在为您安排专员跟进",
            "正在为您安排技术人员处理",
            "正在为您转接相关部门处理",
            "正在为您联系相关工作人员处理",
            "正在为您协调相关部门处理",
            "正在为您跟进处理进度",
            "正在为您反馈处理结果",
            "正在为您升级处理级别",
            "正在为您加急处理问题",
            "正在为您优先处理请求",
            "正在为您安排专员跟进",
            "正在为您安排技术人员处理"
        ]

        # 添加关键词权重
        self.keyword_weights = {
            '支付问题': 1.2,
            '物流问题': 1.1,
            '账户问题': 1.3,
            '商品问题': 1.0,
            '订单问题': 1.2,
            '服务问题': 1.1,
            '系统问题': 1.0,
            '安全隐私': 1.3,
            '优惠活动': 0.8,
            '投诉建议': 1.2,
            'ETC业务': 1.4,
            '车辆相关': 1.2,
            '票据问题': 1.1,
            '紧急问题': 1.5
        }
        
        # 添加关键词重要性权重
        self.importance_weights = {
            'etc': 2.0,
            '支付': 1.8,
            '退款': 1.8,
            '账户': 1.7,
            '密码': 1.7,
            '安全': 1.6,
            '紧急': 1.6,
            '故障': 1.5,
            '错误': 1.5,
            '问题': 1.4,
            '异常': 1.4,
            '无法': 1.4,
            '不能': 1.4,
            '怎么办': 1.3,
            '如何': 1.3,
            '怎么': 1.3,
            '为什么': 1.3,
            '原因': 1.3,
            '解决': 1.3
        }

    def standardize_encoding(self, text: str) -> str:
        """统一编码格式"""
        if not isinstance(text, str):
            return str(text)
        return unicodedata.normalize('NFKC', text)

    def standardize_datetime(self, dt: datetime) -> datetime:
        """标准化日期时间格式"""
        if not isinstance(dt, datetime):
            return dt
        return dt.replace(microsecond=0)

    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not isinstance(text, str):
            return ""
            
        # 标准化文本编码
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # 移除系统标签和特殊字符
        text = re.sub(r'\[.*?\]', '', text)  # 移除方括号及其内容
        text = re.sub(r'<.*?>', '', text)    # 移除HTML标签
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、：；""''（）【】《》\s]', '', text)  # 只保留中文、英文、数字和基本标点
        
        # 移除重复字符
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # 敏感信息脱敏处理
        # 1. 身份证号脱敏（保留前6位和后4位）
        text = re.sub(r'[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]', 
                     lambda m: m.group()[:6] + '*' * 8 + m.group()[-4:], text)
        
        # 2. 手机号脱敏（保留前3位和后4位）
        text = re.sub(r'1[3-9]\d{9}', lambda m: m.group()[:3] + '*' * 4 + m.group()[-4:], text)
        
        # 3. 座机号码脱敏
        text = re.sub(r'(?:\d{3,4}-?)?\d{7,8}', lambda m: '*' * len(m.group()), text)
        
        # 4. 邮箱地址脱敏
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 
                     lambda m: m.group().split('@')[0][:2] + '*' * (len(m.group().split('@')[0])-2) + '@' + m.group().split('@')[1], text)
        
        # 5. 银行卡号脱敏（保留前6位和后4位）
        text = re.sub(r'\d{16,19}', lambda m: m.group()[:6] + '*' * (len(m.group())-10) + m.group()[-4:], text)
        
        # 6. 中文姓名脱敏（保留姓氏）
        text = re.sub(r'[\u4e00-\u9fa5]{2,4}(?=先生|女士|小姐|老师|经理|主任|医生|护士|警官|同志)', 
                     lambda m: m.group()[0] + '*' * (len(m.group())-1), text)
        
        # 7. 地址脱敏（保留省份和城市）
        text = re.sub(r'[\u4e00-\u9fa5]{2,}省[\u4e00-\u9fa5]{2,}市[\u4e00-\u9fa5]{2,}区?[\u4e00-\u9fa5]{2,}号?[\u4e00-\u9fa5]{2,}室?', 
                     lambda m: m.group().split('市')[0] + '市' + '*' * (len(m.group().split('市')[1])), text)
        
        # 8. 车牌号脱敏（保留省份简称和最后两位）
        text = re.sub(r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4,5}[A-Z0-9挂学警港澳]', 
                     lambda m: m.group()[:2] + '*' * (len(m.group())-4) + m.group()[-2:], text)
        
        # 9. 微信号脱敏
        text = re.sub(r'微信号[：:]\s*[a-zA-Z0-9_-]{6,20}', '微信号：******', text)
        
        # 10. QQ号脱敏
        text = re.sub(r'QQ[号：:]\s*[1-9][0-9]{4,}', 'QQ号：******', text)
        
        # 11. 网址脱敏
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
                     lambda m: 'http://******', text)
        
        # 12. 日期时间脱敏（保留年月）
        text = re.sub(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?', lambda m: m.group().split('月')[0] + '月**日', text)
        
        # 移除无效内容
        # 1. 移除纯标点符号
        text = re.sub(r'^[\s\.,，。!！?？]+$', '', text)
        
        # 2. 移除纯英文数字
        text = re.sub(r'^[a-zA-Z0-9\s]+$', '', text)
        
        # 3. 移除系统消息和自动回复（使用模式匹配）
        # 3.1 移除以"正在"开头的处理状态消息
        text = re.sub(r'^正在(?:为您)?(?:处理|查询|核实|办理|审核|转接|联系|协调|跟进|反馈|升级|加急|优先|安排|转派|转办|转达|转告|转述|转报|转呈|转递|转送).*$', '', text)
        
        # 3.2 移除以"请稍"开头的等待提示
        text = re.sub(r'^请稍(?:等|候|后|待).*$', '', text)
        
        # 3.3 移除以"感谢"开头的感谢语
        text = re.sub(r'^感谢(?:您的)?(?:咨询|支持|理解|配合|耐心等待).*$', '', text)
        
        # 3.4 移除以"您好"开头的问候语
        text = re.sub(r'^您好(?:，|,)?(?:很高兴|非常高兴)?(?:为您服务|为您提供帮助).*$', '', text)
        
        # 3.5 移除以"需要"开头的协作提示
        text = re.sub(r'^需要(?:转接|升级|反馈|核实|确认|验证|审核|审批|处理|跟进|协调|沟通|联系|对接|交接|转交|移交|转介|转派|转办|转达|转告|转述|转报|转呈|转递|转送).*$', '', text)
        
        # 3.6 移除以"正在为您"开头的处理提示
        text = re.sub(r'^正在为您(?:处理|查询|核实|办理|审核|转接|联系|协调|跟进|反馈|升级|加急|优先|安排|转派|转办|转达|转告|转述|转报|转呈|转递|转送).*$', '', text)
        
        # 3.7 移除以"系统"开头的系统提示
        text = re.sub(r'^系统(?:正在|正在为您)?(?:处理|查询|核实|办理|审核|转接|联系|协调|跟进|反馈|升级|加急|优先|安排|转派|转办|转达|转告|转述|转报|转呈|转递|转送).*$', '', text)
        
        # 3.8 移除以"正在"开头的状态提示
        text = re.sub(r'^正在(?:加载|同步|下载|上传|连接|处理|查询|核实|办理|审核|转接|联系|协调|跟进|反馈|升级|加急|优先|安排|转派|转办|转达|转告|转述|转报|转呈|转递|转送).*$', '', text)
        
        # 3.9 移除以"已"开头的状态提示
        text = re.sub(r'^已(?:读|送达|发送|处理|完成|成功|失败|取消|删除|清空|置顶|静音|屏蔽|拉黑|举报|关注|取消关注|点赞|收藏).*$', '', text)
        
        # 3.10 移除以"正在为您"开头的处理提示（带时间）
        text = re.sub(r'^正在为您(?:处理|查询|核实|办理|审核|转接|联系|协调|跟进|反馈|升级|加急|优先|安排|转派|转办|转达|转告|转述|转报|转呈|转递|转送).*?，请稍候.*$', '', text)
        
        # 4. 移除其他无效内容
        # 4.1 移除纯表情符号
        text = re.sub(r'^[\U0001F300-\U0001F9FF\s]+$', '', text)
        
        # 4.2 移除纯数字和标点
        text = re.sub(r'^[\d\s\.,，。!！?？]+$', '', text)
        
        # 4.3 移除纯英文和标点
        text = re.sub(r'^[a-zA-Z\s\.,，。!！?？]+$', '', text)
        
        # 4.4 移除纯中文标点
        text = re.sub(r'^[\s，。！？、：；""''（）【】《》]+$', '', text)
        
        # 4.5 移除纯空格和换行
        text = re.sub(r'^[\s\n]+$', '', text)
        
        # 4.6 移除重复的标点符号
        text = re.sub(r'([，。！？、：；""''（）【】《》])\1+', r'\1', text)
        
        # 4.7 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        # 标准化标点符号
        text = text.replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?')
        text = text.replace('：', ':').replace('；', ';').replace('（', '(').replace('）', ')')
        text = text.replace('【', '[').replace('】', ']').replace('《', '<').replace('》', '>')
        
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

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
            
        # 4. 检查是否只包含标点符号
        if re.match(r'^[\s\.,，。!！?？]+$', text):
            return False
            
        # 5. 检查是否只包含英文数字
        if re.match(r'^[a-zA-Z0-9\s]+$', text):
            return False
            
        # 6. 检查是否包含系统消息特征
        if re.search(r'系统|提示|通知|公告|消息|提醒', text):
            return False
            
        # 7. 检查是否包含自动回复特征
        if re.search(r'您好|感谢|谢谢|再见|欢迎|客服', text) and len(text) < 10:
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

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算文本的语义相似度"""
        if not text1 or not text2:
            return 0.0
            
        # 1. 分词并计算词频
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 2. 计算Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        if union == 0:
            return 0.0
        jaccard = intersection / union
        
        # 3. 计算关键词匹配度
        keyword_matches = 0
        total_keywords = 0
        
        for word in words1:
            if word in self.importance_weights:
                total_keywords += 1
                if word in words2:
                    keyword_matches += 1
                    
        for word in words2:
            if word in self.importance_weights:
                total_keywords += 1
                if word in words1:
                    keyword_matches += 1
                    
        keyword_similarity = keyword_matches / total_keywords if total_keywords > 0 else 0.0
        
        # 4. 综合计算相似度
        return 0.6 * jaccard + 0.4 * keyword_similarity

    def calculate_context_match(self, question: str, answer: str) -> float:
        """计算问题和回答的上下文匹配度"""
        # 获取问题和回答的标签
        question_tags = self.extract_tags(question)
        answer_tags = self.extract_tags(answer)
        
        # 计算标签匹配度
        matching_tags = set(question_tags) & set(answer_tags)
        tag_match_score = len(matching_tags) / max(len(question_tags), len(answer_tags)) if question_tags or answer_tags else 0
        
        # 计算关键词匹配度
        question_keywords = set()
        answer_keywords = set()
        
        # 从问题和回答中提取关键词
        for category, keywords in self.context_keywords.items():
            for keyword in keywords:
                if keyword in question:
                    question_keywords.add(category)
                if keyword in answer:
                    answer_keywords.add(category)
        
        # 计算关键词匹配度
        matching_keywords = question_keywords & answer_keywords
        keyword_match_score = len(matching_keywords) / max(len(question_keywords), len(answer_keywords)) if question_keywords or answer_keywords else 0
        
        # 计算语义相似度
        semantic_score = self.calculate_semantic_similarity(question, answer)
        
        # 综合计算匹配分数（加权平均）
        match_score = (
            0.4 * tag_match_score +      # 标签匹配度权重
            0.3 * keyword_match_score +  # 关键词匹配度权重
            0.3 * semantic_score         # 语义相似度权重
        )
        
        return match_score

    def is_context_match(self, question: str, answer: str, threshold: float = 0.3) -> bool:
        """判断问题和回答的语境是否匹配"""
        match_score = self.calculate_context_match(question, answer)
        return match_score >= threshold 