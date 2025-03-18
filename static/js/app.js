/**
 * 校园众创平台主脚本文件
 */

// 等待文档加载完成
$(document).ready(function() {
    
    // 初始化提示工具
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 自动隐藏警告信息
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // 响应式导航栏调整
    $(window).on('resize', function() {
        if ($(window).width() < 768) {
            $('.navbar-collapse').addClass('small-nav');
        } else {
            $('.navbar-collapse').removeClass('small-nav');
        }
    });
    
    // 回到顶部按钮
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            $('#back-to-top').fadeIn();
        } else {
            $('#back-to-top').fadeOut();
        }
    });
    
    // 点击回到顶部
    $('#back-to-top').click(function() {
        $('html, body').animate({scrollTop: 0}, 800);
        return false;
    });
    
    // 表单验证
    $('.needs-validation').submit(function(event) {
        if (this.checkValidity() === false) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // 动态内容加载动画
    $(document).on('click', '.load-more', function(e) {
        e.preventDefault();
        var $this = $(this);
        var $content = $this.data('target');
        
        $this.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 加载中...');
        
        // 模拟加载延迟
        setTimeout(function() {
            // 在真实应用中，这里应该是一个AJAX请求
            $this.html('加载更多');
        }, 1500);
    });
    
    // 搜索框交互
    $('.search-toggle').click(function() {
        $('.search-form').toggleClass('active');
        $('#search-input').focus();
    });
    
    // 切换列表/网格视图
    $('.view-switch').click(function() {
        var target = $(this).data('target');
        $(this).addClass('active').siblings().removeClass('active');
        
        if ($(this).data('view') === 'list') {
            $(target).removeClass('grid-view').addClass('list-view');
        } else {
            $(target).removeClass('list-view').addClass('grid-view');
        }
    });
    
    // 筛选面板切换
    $('.filter-toggle').click(function() {
        $('.filter-panel').toggleClass('show');
    });
    
    // 图片预览
    $('.image-preview').click(function() {
        var src = $(this).data('src');
        var title = $(this).data('title');
        
        $('#image-preview-modal .modal-title').text(title);
        $('#image-preview-modal .preview-image').attr('src', src);
        $('#image-preview-modal').modal('show');
    });
    
    // 确认对话框
    $('.confirm-action').click(function(e) {
        e.preventDefault();
        
        var $this = $(this);
        var message = $this.data('confirm') || '确定要执行此操作吗？';
        
        if (confirm(message)) {
            if ($this.is('a')) {
                window.location = $this.attr('href');
            } else if ($this.is('button')) {
                $this.closest('form').submit();
            }
        }
    });
    
    // 添加动画效果
    $('.animate-on-scroll').each(function() {
        var $this = $(this);
        
        $(window).scroll(function() {
            var top_of_element = $this.offset().top;
            var bottom_of_element = $this.offset().top + $this.outerHeight();
            var bottom_of_screen = $(window).scrollTop() + $(window).innerHeight();
            var top_of_screen = $(window).scrollTop();
            
            if ((bottom_of_screen > top_of_element) && (top_of_screen < bottom_of_element)) {
                $this.addClass('animated');
            }
        });
    });
}); 