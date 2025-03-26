"""支付模块异常类"""

class PaymentError(Exception):
    """支付基础异常类"""
    pass

class PaymentValidationError(PaymentError):
    """支付验证错误"""
    pass

class PaymentAmountError(PaymentValidationError):
    """支付金额错误"""
    pass

class PaymentMethodError(PaymentValidationError):
    """支付方式错误"""
    pass

class PaymentTimeoutError(PaymentError):
    """支付超时错误"""
    pass

class PaymentSignatureError(PaymentError):
    """支付签名错误"""
    pass

class PaymentCallbackError(PaymentError):
    """支付回调错误"""
    pass

class PaymentStatusError(PaymentError):
    """支付状态错误"""
    pass

class PaymentRefundError(PaymentError):
    """支付退款错误"""
    pass 