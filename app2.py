from flask import Flask, render_template_string
import os

# 设置环境变量禁用dotenv自动加载
os.environ['FLASK_SKIP_DOTENV'] = '1'

app = Flask(__name__)

@app.route('/')
def index():
    template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>复旦创新创业平台</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #3f51b5;
            }
            p {
                font-size: 18px;
                color: #555;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background-color: #3f51b5;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>复旦创新创业平台</h1>
            <p>平台已成功启动！</p>
            <p>这是一个临时的首页，用于测试应用是否正常运行。</p>
            <a href="/about" class="btn">了解更多</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/about')
def about():
    template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>关于我们 - 复旦创新创业平台</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: left;
            }
            h1 {
                color: #3f51b5;
                text-align: center;
            }
            p {
                font-size: 16px;
                color: #555;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background-color: #3f51b5;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 20px;
                font-weight: bold;
            }
            .center {
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>关于复旦创新创业平台</h1>
            <p>复旦创新创业平台是一个支持复旦大学学生创新创业项目的平台，旨在为学生提供项目展示、团队组建、众筹支持等功能。</p>
            <p>我们的目标是：</p>
            <ul>
                <li>促进校园创新文化</li>
                <li>帮助学生实现创意</li>
                <li>连接创业者与支持者</li>
                <li>培养创新创业人才</li>
            </ul>
            <p>该平台提供众筹项目展示、团队组建、支付中心等功能，让创新创业变得更加简单。</p>
            <div class="center">
                <a href="/" class="btn">返回首页</a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    print("启动独立应用...")
    app.run(debug=True, port=5001) 