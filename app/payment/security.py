"""支付安全验证功能"""
from flask import current_app, request
from app.payment.exceptions import PaymentValidationError, PaymentSignatureError
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

def verify_payment_request():
    """验证支付请求"""
    try:
        # 验证请求时间戳
        timestamp = request.headers.get('X-Payment-Timestamp')
        if not timestamp:
            raise PaymentValidationError('缺少时间戳')
            
        try:
            timestamp = int(timestamp)
        except ValueError:
            raise PaymentValidationError('无效的时间戳')
            
        # 检查时间戳是否在有效期内(5分钟)
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:
            raise PaymentValidationError('请求已过期')
            
        # 验证签名
        signature = request.headers.get('X-Payment-Signature')
        if not signature:
            raise PaymentValidationError('缺少签名')
            
        # 获取请求数据
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # 验证签名
        if not verify_signature(data, signature):
            raise PaymentSignatureError('签名验证失败')
            
        # 验证IP白名单
        client_ip = request.remote_addr
        if not verify_ip_whitelist(client_ip):
            raise PaymentValidationError('IP地址不在白名单内')
            
        return True
        
    except Exception as e:
        logger.error(f"支付请求验证失败: {str(e)}")
        raise

def verify_signature(data, signature):
    """验证签名"""
    try:
        # 获取签名密钥
        secret_key = current_app.config.get('PAYMENT_SECRET_KEY')
        if not secret_key:
            logger.error("未配置支付签名密钥")
            return False
            
        # 按字母顺序排序参数
        sorted_params = sorted(data.items())
        
        # 拼接参数
        sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 添加密钥
        sign_str += f"&key={secret_key}"
        
        # 计算MD5
        calculated_signature = hashlib.md5(sign_str.encode()).hexdigest().upper()
        
        # 验证签名
        return calculated_signature == signature
        
    except Exception as e:
        logger.error(f"签名验证失败: {str(e)}")
        return False

def verify_ip_whitelist(ip):
    """验证IP白名单"""
    try:
        # 获取IP白名单
        whitelist = current_app.config.get('PAYMENT_IP_WHITELIST', [])
        
        # 如果是空列表,表示不限制IP
        if not whitelist:
            return True
            
        # 检查IP是否在白名单内
        return ip in whitelist
        
    except Exception as e:
        logger.error(f"IP白名单验证失败: {str(e)}")
        return False

def generate_payment_token(payment_id, amount):
    """生成支付令牌"""
    try:
        # 获取密钥
        secret_key = current_app.config.get('PAYMENT_SECRET_KEY')
        if not secret_key:
            logger.error("未配置支付签名密钥")
            return None
            
        # 生成时间戳
        timestamp = int(time.time())
        
        # 构建签名字符串
        sign_str = f"{payment_id}&{amount}&{timestamp}&{secret_key}"
        
        # 计算签名
        signature = hashlib.md5(sign_str.encode()).hexdigest().upper()
        
        # 返回令牌
        return {
            'payment_id': payment_id,
            'amount': amount,
            'timestamp': timestamp,
            'signature': signature
        }
        
    except Exception as e:
        logger.error(f"生成支付令牌失败: {str(e)}")
        return None

def verify_payment_token(token):
    """验证支付令牌"""
    try:
        # 验证必要参数
        if not all(k in token for k in ['payment_id', 'amount', 'timestamp', 'signature']):
            return False
            
        # 验证时间戳
        current_time = int(time.time())
        if abs(current_time - token['timestamp']) > 300:
            return False
            
        # 获取密钥
        secret_key = current_app.config.get('PAYMENT_SECRET_KEY')
        if not secret_key:
            return False
            
        # 构建签名字符串
        sign_str = f"{token['payment_id']}&{token['amount']}&{token['timestamp']}&{secret_key}"
        
        # 计算签名
        calculated_signature = hashlib.md5(sign_str.encode()).hexdigest().upper()
        
        # 验证签名
        return calculated_signature == token['signature']
        
    except Exception as e:
        logger.error(f"验证支付令牌失败: {str(e)}")
        return False 