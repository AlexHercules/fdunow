"""
测试邮件发送功能
"""
import unittest
from flask import current_app
from application import create_app, mail
from flask_mail import Message

class MailTestCase(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
    
    def tearDown(self):
        """测试后的清理工作"""
        self.app_context.pop()
    
    def test_mail_config(self):
        """测试邮件配置是否正确"""
        self.assertTrue(current_app.config['TESTING'])
        self.assertIsNotNone(current_app.config['MAIL_SERVER'])
        self.assertIsNotNone(current_app.config['MAIL_PORT'])
        self.assertIsNotNone(current_app.config['MAIL_USERNAME'])
        self.assertIsNotNone(current_app.config['MAIL_PASSWORD'])
    
    def test_mail_api(self):
        """测试邮件API是否正常响应"""
        response = self.client.post('/mail/test',
                                    json={'email': 'test@example.com'})
        json_data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', json_data)
        # 注意：在测试环境中，实际邮件不会被发送
        # 所以只测试API响应是否正确
    
    def test_send_verification_code(self):
        """测试发送验证码功能"""
        response = self.client.post('/auth/send_verification_code',
                                    json={'email': 'test@example.com'})
        json_data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', json_data)

if __name__ == '__main__':
    unittest.main() 