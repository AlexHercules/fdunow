/**
 * 支付表单组件
 * 提供多种支付方式选择和支付处理功能
 */
class PaymentForm {
  /**
   * 构造函数
   * @param {Object} options - 配置项
   * @param {string} options.elementId - 表单容器元素ID
   * @param {number} options.projectId - 项目ID
   * @param {string} options.projectTitle - 项目标题
   * @param {Function} options.onSuccess - 支付成功回调
   * @param {Function} options.onFailure - 支付失败回调
   * @param {Function} options.onCancel - 取消支付回调
   */
  constructor(options) {
    this.elementId = options.elementId;
    this.projectId = options.projectId;
    this.projectTitle = options.projectTitle;
    this.onSuccess = options.onSuccess || function() {};
    this.onFailure = options.onFailure || function() {};
    this.onCancel = options.onCancel || function() {};
    
    this.element = document.getElementById(this.elementId);
    if (!this.element) {
      console.error(`找不到ID为${this.elementId}的元素`);
      return;
    }
    
    this.amount = 0;
    this.selectedPaymentMethod = null;
    this.transaction = null;
    
    this.init();
  }
  
  /**
   * 初始化表单
   */
  init() {
    this.render();
    this.attachEventListeners();
  }
  
  /**
   * 渲染表单
   */
  render() {
    // 支付方式列表
    const paymentMethods = [
      { id: 'alipay', name: '支付宝', icon: 'fab fa-alipay' },
      { id: 'wechat', name: '微信支付', icon: 'fab fa-weixin' },
      { id: 'campus_card', name: '校园卡', icon: 'fas fa-id-card' },
      { id: 'bank_transfer', name: '银行转账', icon: 'fas fa-university' }
    ];
    
    // 金额选项
    const amountOptions = [
      { value: 10, label: '¥10' },
      { value: 50, label: '¥50' },
      { value: 100, label: '¥100' },
      { value: 200, label: '¥200' },
      { value: 500, label: '¥500' },
      { value: 'custom', label: '自定义' }
    ];
    
    // 构建表单HTML
    let html = `
      <div class="payment-form card">
        <div class="card-header">
          <h5>支持项目: ${this.projectTitle}</h5>
        </div>
        <div class="card-body">
          <form id="donation-form">
            <div class="form-group mb-4">
              <label class="form-label">选择金额</label>
              <div class="amount-options d-flex flex-wrap">
    `;
    
    // 添加金额选项
    amountOptions.forEach(option => {
      html += `
        <div class="amount-option m-1">
          <input type="radio" name="amount" id="amount-${option.value}" value="${option.value}" class="btn-check" ${option.value === 50 ? 'checked' : ''}>
          <label for="amount-${option.value}" class="btn btn-outline-primary">${option.label}</label>
        </div>
      `;
    });
    
    // 添加自定义金额输入框
    html += `
              </div>
              <div id="custom-amount-container" class="mt-3" style="display: none;">
                <input type="number" id="custom-amount" class="form-control" placeholder="请输入金额" min="1" step="1">
              </div>
            </div>
            
            <div class="form-group mb-4">
              <label class="form-label">选择支付方式</label>
              <div class="payment-methods">
    `;
    
    // 添加支付方式选项
    paymentMethods.forEach(method => {
      html += `
        <div class="payment-method-option mb-2">
          <input type="radio" name="payment-method" id="payment-${method.id}" value="${method.id}" class="form-check-input" ${method.id === 'alipay' ? 'checked' : ''}>
          <label for="payment-${method.id}" class="form-check-label">
            <i class="${method.icon}"></i> ${method.name}
          </label>
        </div>
      `;
    });
    
    // 添加留言和提交按钮
    html += `
              </div>
            </div>
            
            <div class="form-group mb-4">
              <label for="donation-message" class="form-label">留言(可选)</label>
              <textarea id="donation-message" class="form-control" rows="2" placeholder="写下您的支持和鼓励"></textarea>
            </div>
            
            <div class="form-group d-grid">
              <button type="submit" id="submit-payment" class="btn btn-primary btn-lg">立即支付</button>
            </div>
          </form>
        </div>
        
        <div id="payment-processing" class="card-body text-center" style="display: none;">
          <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">处理中...</span>
          </div>
          <h5>正在处理支付，请稍候...</h5>
        </div>
        
        <div id="payment-qrcode" class="card-body text-center" style="display: none;">
          <div class="qrcode-container mb-3">
            <div id="qrcode"></div>
          </div>
          <p>请使用<span id="payment-method-name"></span>扫描二维码完成支付</p>
          <p><small>支付金额: ¥<span id="payment-amount"></span></small></p>
          <div class="mt-3">
            <button id="payment-complete" class="btn btn-success me-2">我已完成支付</button>
            <button id="payment-cancel" class="btn btn-outline-secondary">取消支付</button>
          </div>
        </div>
        
        <div id="payment-result" class="card-body text-center" style="display: none;">
          <div id="payment-success" style="display: none;">
            <i class="fas fa-check-circle text-success fs-1 mb-3"></i>
            <h4>支付成功</h4>
            <p>感谢您对项目的支持！</p>
          </div>
          <div id="payment-failure" style="display: none;">
            <i class="fas fa-times-circle text-danger fs-1 mb-3"></i>
            <h4>支付失败</h4>
            <p id="payment-error-message">支付处理时发生错误，请稍后重试。</p>
          </div>
          <div class="mt-3">
            <button id="payment-done" class="btn btn-primary">完成</button>
          </div>
        </div>
      </div>
    `;
    
    this.element.innerHTML = html;
  }
  
  /**
   * 添加事件监听器
   */
  attachEventListeners() {
    // 获取元素引用
    const form = document.getElementById('donation-form');
    const customAmountRadio = document.getElementById('amount-custom');
    const customAmountContainer = document.getElementById('custom-amount-container');
    const customAmountInput = document.getElementById('custom-amount');
    const submitButton = document.getElementById('submit-payment');
    const paymentComplete = document.getElementById('payment-complete');
    const paymentCancel = document.getElementById('payment-cancel');
    const paymentDone = document.getElementById('payment-done');
    
    // 处理自定义金额选项显示逻辑
    document.querySelectorAll('input[name="amount"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
          customAmountContainer.style.display = 'block';
          customAmountInput.focus();
        } else {
          customAmountContainer.style.display = 'none';
          this.amount = parseInt(e.target.value);
        }
      });
    });
    
    // 监听自定义金额输入
    customAmountInput.addEventListener('input', (e) => {
      this.amount = parseInt(e.target.value) || 0;
    });
    
    // 选择支付方式
    document.querySelectorAll('input[name="payment-method"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.selectedPaymentMethod = e.target.value;
      });
    });
    
    // 设置默认选择
    this.amount = 50; // 默认金额
    this.selectedPaymentMethod = 'alipay'; // 默认支付方式
    
    // 表单提交处理
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      
      // 验证金额
      if (this.amount <= 0) {
        alert('请输入有效的捐款金额');
        return;
      }
      
      // 获取留言
      const message = document.getElementById('donation-message').value;
      
      // 显示处理中状态
      this.showProcessingState();
      
      // 创建捐款交易
      this.createDonation(this.amount, this.selectedPaymentMethod, message);
    });
    
    // 完成支付按钮
    paymentComplete.addEventListener('click', () => {
      this.completePayment();
    });
    
    // 取消支付按钮
    paymentCancel.addEventListener('click', () => {
      this.cancelPayment();
    });
    
    // 支付结果完成按钮
    paymentDone.addEventListener('click', () => {
      // 重置表单
      form.reset();
      
      // 显示表单状态
      this.showFormState();
      
      // 回调
      if (this.transaction && this.transaction.status === 'completed') {
        this.onSuccess(this.transaction);
      } else {
        this.onCancel();
      }
    });
  }
  
  /**
   * 创建捐款交易
   * @param {number} amount - 金额
   * @param {string} paymentMethod - 支付方式
   * @param {string} message - 留言
   */
  createDonation(amount, paymentMethod, message) {
    const data = {
      project_id: this.projectId,
      amount: amount,
      payment_method: paymentMethod,
      description: message || undefined
    };
    
    fetch('/api/donations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken()
      },
      body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
      if (data.transaction) {
        this.transaction = data.transaction;
        this.showQRCodeState();
      } else {
        throw new Error(data.error || '创建捐款失败');
      }
    })
    .catch(error => {
      console.error('创建捐款失败:', error);
      this.showFailureState(error.message);
    });
  }
  
  /**
   * 完成支付处理
   */
  completePayment() {
    if (!this.transaction) {
      this.showFailureState('交易信息丢失');
      return;
    }
    
    // 显示处理中状态
    this.showProcessingState();
    
    // 模拟支付网关回调
    fetch(`/api/donations/${this.transaction.id}/pay`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken()
      },
      body: JSON.stringify({
        payment_method: this.selectedPaymentMethod,
        payment_time: new Date().toISOString()
      })
    })
    .then(response => response.json())
    .then(data => {
      this.transaction = data.transaction;
      
      if (data.message === '支付成功') {
        this.showSuccessState();
      } else {
        throw new Error(data.message || '支付处理失败');
      }
    })
    .catch(error => {
      console.error('支付处理失败:', error);
      this.showFailureState(error.message);
    });
  }
  
  /**
   * 取消支付
   */
  cancelPayment() {
    this.showFormState();
    this.onCancel();
  }
  
  /**
   * 显示表单状态
   */
  showFormState() {
    document.getElementById('donation-form').style.display = 'block';
    document.getElementById('payment-processing').style.display = 'none';
    document.getElementById('payment-qrcode').style.display = 'none';
    document.getElementById('payment-result').style.display = 'none';
  }
  
  /**
   * 显示处理中状态
   */
  showProcessingState() {
    document.getElementById('donation-form').style.display = 'none';
    document.getElementById('payment-processing').style.display = 'block';
    document.getElementById('payment-qrcode').style.display = 'none';
    document.getElementById('payment-result').style.display = 'none';
  }
  
  /**
   * 显示二维码支付状态
   */
  showQRCodeState() {
    document.getElementById('donation-form').style.display = 'none';
    document.getElementById('payment-processing').style.display = 'none';
    document.getElementById('payment-qrcode').style.display = 'block';
    document.getElementById('payment-result').style.display = 'none';
    
    // 更新支付信息
    document.getElementById('payment-method-name').textContent = this.getPaymentMethodName(this.selectedPaymentMethod);
    document.getElementById('payment-amount').textContent = this.amount;
    
    // 生成二维码（使用模拟数据）
    this.generateQRCode(`donate:${this.projectId}:${this.transaction.id}:${this.amount}`);
  }
  
  /**
   * 显示成功状态
   */
  showSuccessState() {
    document.getElementById('donation-form').style.display = 'none';
    document.getElementById('payment-processing').style.display = 'none';
    document.getElementById('payment-qrcode').style.display = 'none';
    document.getElementById('payment-result').style.display = 'block';
    
    document.getElementById('payment-success').style.display = 'block';
    document.getElementById('payment-failure').style.display = 'none';
  }
  
  /**
   * 显示失败状态
   * @param {string} errorMessage - 错误信息
   */
  showFailureState(errorMessage) {
    document.getElementById('donation-form').style.display = 'none';
    document.getElementById('payment-processing').style.display = 'none';
    document.getElementById('payment-qrcode').style.display = 'none';
    document.getElementById('payment-result').style.display = 'block';
    
    document.getElementById('payment-success').style.display = 'none';
    document.getElementById('payment-failure').style.display = 'block';
    
    if (errorMessage) {
      document.getElementById('payment-error-message').textContent = errorMessage;
    }
  }
  
  /**
   * 生成二维码
   * @param {string} data - 二维码数据
   */
  generateQRCode(data) {
    const qrcodeElement = document.getElementById('qrcode');
    qrcodeElement.innerHTML = '';
    
    // 如果已加载QRCode库则使用
    if (window.QRCode) {
      new QRCode(qrcodeElement, {
        text: data,
        width: 200,
        height: 200
      });
    } else {
      // 否则显示模拟图片
      qrcodeElement.innerHTML = `
        <div class="mock-qrcode" style="width:200px;height:200px;background:#f5f5f5;display:flex;align-items:center;justify-content:center;border:1px solid #ddd;">
          <span>模拟二维码</span>
        </div>
      `;
      
      // 动态加载QRCode库
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js';
      script.onload = () => this.generateQRCode(data);
      document.head.appendChild(script);
    }
  }
  
  /**
   * 获取支付方式名称
   * @param {string} methodId - 支付方式ID
   * @returns {string} 支付方式名称
   */
  getPaymentMethodName(methodId) {
    const methodMap = {
      'alipay': '支付宝',
      'wechat': '微信',
      'campus_card': '校园卡',
      'bank_transfer': '银行转账'
    };
    
    return methodMap[methodId] || methodId;
  }
  
  /**
   * 获取CSRF Token
   * @returns {string} CSRF Token
   */
  getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  }
}

// 导出组件
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PaymentForm;
} 