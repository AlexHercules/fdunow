from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
import random
import string
import uuid
from flask import current_app
from app.extensions import db

from app.payment.models import (
    Transaction, TransactionType, TransactionStatus,
    ServiceFee, Invoice, Refund, RefundStatus, PaymentMethod, Dispute
)

class PaymentService:
    """支付服务类，处理支付相关业务逻辑"""
    
    @staticmethod
    def create_donation(user_id, project_id, amount, payment_method, description=None):
        """创建捐款交易
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            amount: 捐款金额
            payment_method: 支付方式
            description: 描述信息
            
        Returns:
            Transaction: 创建的交易实�?
        """
        # 验证输入
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError("金额必须大于0")
        except (ValueError, TypeError, decimal.InvalidOperation):
            raise ValueError("无效的金额格�?)
            
        # 生成唯一交易标识
        payment_reference = f"DON-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # 创建交易记录
        transaction = Transaction(
            transaction_type=TransactionType.DONATION.value,
            amount=amount,
            description=description or f"捐款支持项目",
            payment_method=payment_method,
            payment_reference=payment_reference,
            status=TransactionStatus.PENDING.value,
            user_id=user_id,
            project_id=project_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def process_payment(transaction_id, payment_data):
        """处理支付
        
        模拟与支付网关的交互，处理支付结�?
        
        Args:
            transaction_id: 交易ID
            payment_data: 支付数据，包含支付信�?
            
        Returns:
            bool: 支付是否成功
        """
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError("交易不存�?)
            
        if transaction.status != TransactionStatus.PENDING.value:
            raise ValueError("交易状态不允许支付处理")
            
        # 模拟支付网关处理
        # 实际项目中，这里会对接支付网关API
        success = random.random() > 0.1  # 模拟90%成功�?
        
        if success:
            transaction.status = TransactionStatus.COMPLETED.value
            
            # 如果是捐款，计算并记录服务费
            if transaction.transaction_type == TransactionType.DONATION.value:
                # 获取项目类别
                project = transaction.project
                if project:
                    fee_amount, fee_percentage = ServiceFee.calculate_fee(
                        transaction.amount, project.category
                    )
                    
                    # 创建服务费记�?
                    service_fee = ServiceFee(
                        amount=fee_amount,
                        percentage=fee_percentage,
                        description=f"项目服务�? {project.title}",
                        transaction_id=transaction.id,
                        project_id=project.id
                    )
                    
                    db.session.add(service_fee)
            
            # 更新项目筹款进度
            project = transaction.project
            if project:
                # 计算项目当前筹款总额
                total_raised = db.session.query(db.func.sum(Transaction.amount))\
                    .filter(Transaction.project_id == project.id,
                           Transaction.transaction_type == TransactionType.DONATION.value,
                           Transaction.status == TransactionStatus.COMPLETED.value)\
                    .scalar() or Decimal('0')
                
                project.current_amount = total_raised
                
                # 检查是否达到目标金�?
                if project.status == 'fundraising' and total_raised >= project.target_amount:
                    project.status = 'funded'
                    
                    # 创建结算账单
                    Invoice.create_from_project(project)
        else:
            transaction.status = TransactionStatus.FAILED.value
            
        # 保存支付结果元数�?
        transaction.metadata_dict = {
            **transaction.metadata_dict,
            "payment_result": "success" if success else "failed",
            "payment_time": datetime.utcnow().isoformat(),
            "payment_data": payment_data
        }
        
        db.session.commit()
        return success
    
    @staticmethod
    def request_refund(transaction_id, user_id, reason, evidence_urls=None):
        """申请退�?
        
        Args:
            transaction_id: 交易ID
            user_id: 申请用户ID
            reason: 退款原�?
            evidence_urls: 证据文件URL列表
            
        Returns:
            Refund: 创建的退款请求实�?
        """
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError("交易不存�?)
            
        if transaction.status != TransactionStatus.COMPLETED.value:
            raise ValueError("只有已完成的交易才能申请退�?)
            
        if transaction.transaction_type != TransactionType.DONATION.value:
            raise ValueError("只有捐款交易可以申请退�?)
            
        # 检查是否已经有退款申�?
        existing_refund = Refund.query.filter_by(
            transaction_id=transaction_id,
            status=RefundStatus.PENDING.value
        ).first()
        
        if existing_refund:
            raise ValueError("该交易已有待处理的退款申�?)
            
        # 创建退款申请实�?
        refund = Refund()
        
        # 计算退款金额和百分�?
        refund_amount, refund_percentage = refund.calculate_refund_amount(transaction)
        
        refund.transaction_id = transaction_id
        refund.requester_id = user_id
        refund.amount = refund_amount
        refund.refund_percentage = refund_percentage
        refund.reason = reason
        
        if evidence_urls:
            refund.evidence_list = evidence_urls
        
        db.session.add(refund)
        db.session.commit()
        
        return refund
    
    @staticmethod
    def process_refund(refund_id, approver_id, approve=True, admin_notes=None):
        """处理退款申�?
        
        Args:
            refund_id: 退款申请ID
            approver_id: 处理人ID
            approve: 是否批准
            admin_notes: 处理备注
            
        Returns:
            bool: 操作是否成功
        """
        refund = Refund.query.get(refund_id)
        if not refund:
            raise ValueError("退款申请不存在")
            
        if approve:
            success = refund.approve(approver_id, admin_notes)
            
            if success:
                # 更新原交易状�?
                transaction = refund.transaction
                transaction.status = TransactionStatus.REFUNDED.value
                
                # 异步处理实际退款操�?
                # 这里应该调用外部支付网关的退款API
                # 在实际项目中，这应该放在队列任务中处�?
                # background_tasks.process_actual_refund.delay(refund.id)
        else:
            success = refund.reject(approver_id, admin_notes)
        
        db.session.commit()
        return success
    
    @staticmethod
    def create_dispute(complainant_id, title, description, transaction_id=None, refund_id=None, respondent_id=None):
        """创建争议
        
        Args:
            complainant_id: 投诉人ID
            title: 争议标题
            description: 争议描述
            transaction_id: 交易ID（可选）
            refund_id: 退款申请ID（可选）
            respondent_id: 被投诉人ID（可选）
            
        Returns:
            Dispute: 创建的争议实�?
        """
        if not transaction_id and not refund_id:
            raise ValueError("必须提供交易ID或退款申请ID")
            
        # 创建争议实例
        dispute = Dispute(
            title=title,
            description=description,
            status='open',
            complainant_id=complainant_id,
            transaction_id=transaction_id,
            refund_id=refund_id,
            respondent_id=respondent_id
        )
        
        db.session.add(dispute)
        db.session.commit()
        
        return dispute
    
    @staticmethod
    def resolve_dispute(dispute_id, resolver_id, resolution, status='resolved'):
        """解决争议
        
        Args:
            dispute_id: 争议ID
            resolver_id: 解决者ID
            resolution: 解决方案
            status: 解决状�?
            
        Returns:
            bool: 操作是否成功
        """
        dispute = Dispute.query.get(dispute_id)
        if not dispute:
            raise ValueError("争议不存�?)
            
        success = dispute.resolve(resolver_id, resolution, status)
        
        if success:
            db.session.commit()
            
        return success

class FinancialReportService:
    """财务报表服务类，生成各类财务报表"""
    
    @staticmethod
    def get_project_financial_summary(project_id):
        """获取项目财务摘要
        
        Args:
            project_id: 项目ID
            
        Returns:
            dict: 项目财务摘要
        """
        # 获取项目总捐款额
        total_donations = db.session.query(db.func.sum(Transaction.amount))\
            .filter(Transaction.project_id == project_id,
                   Transaction.transaction_type == TransactionType.DONATION.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or Decimal('0')
        
        # 获取已退款金�?
        total_refunds = db.session.query(db.func.sum(Transaction.amount))\
            .filter(Transaction.project_id == project_id,
                   Transaction.transaction_type == TransactionType.REFUND.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or Decimal('0')
        
        # 获取服务费总额
        total_fees = db.session.query(db.func.sum(ServiceFee.amount))\
            .filter(ServiceFee.project_id == project_id)\
            .scalar() or Decimal('0')
        
        # 计算净收入
        net_income = total_donations - total_refunds - total_fees
        
        # 获取捐款人数
        donor_count = db.session.query(db.func.count(db.func.distinct(Transaction.user_id)))\
            .filter(Transaction.project_id == project_id,
                   Transaction.transaction_type == TransactionType.DONATION.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or 0
        
        return {
            'project_id': project_id,
            'total_donations': float(total_donations),
            'total_refunds': float(total_refunds),
            'total_fees': float(total_fees),
            'net_income': float(net_income),
            'donor_count': donor_count
        }
    
    @staticmethod
    def get_platform_financial_summary(start_date=None, end_date=None):
        """获取平台财务摘要
        
        Args:
            start_date: 开始日�?(可�?
            end_date: 结束日期 (可�?
            
        Returns:
            dict: 平台财务摘要
        """
        # 设置默认时间范围为最�?0�?
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        query_filter = Transaction.created_at.between(start_date, end_date)
        
        # 获取总捐款额
        total_donations = db.session.query(db.func.sum(Transaction.amount))\
            .filter(query_filter,
                   Transaction.transaction_type == TransactionType.DONATION.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or Decimal('0')
        
        # 获取已退款金�?
        total_refunds = db.session.query(db.func.sum(Transaction.amount))\
            .filter(query_filter,
                   Transaction.transaction_type == TransactionType.REFUND.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or Decimal('0')
        
        # 获取服务费总额
        total_fees = db.session.query(db.func.sum(ServiceFee.amount))\
            .join(Transaction, ServiceFee.transaction_id == Transaction.id)\
            .filter(Transaction.created_at.between(start_date, end_date))\
            .scalar() or Decimal('0')
        
        # 获取成功的项目数
        successful_projects = db.session.query(db.func.count(db.func.distinct(Transaction.project_id)))\
            .filter(query_filter,
                   Transaction.transaction_type == TransactionType.DONATION.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or 0
        
        # 获取捐款人数
        donor_count = db.session.query(db.func.count(db.func.distinct(Transaction.user_id)))\
            .filter(query_filter,
                   Transaction.transaction_type == TransactionType.DONATION.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .scalar() or 0
        
        # 获取平均捐款金额
        avg_donation = Decimal('0')
        if donor_count > 0:
            avg_donation = total_donations / donor_count
        
        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_donations': float(total_donations),
            'total_refunds': float(total_refunds),
            'total_fees': float(total_fees),
            'net_revenue': float(total_fees - total_refunds),
            'successful_projects': successful_projects,
            'donor_count': donor_count,
            'avg_donation': float(avg_donation)
        }
    
    @staticmethod
    def get_transaction_report(filters=None, page=1, per_page=20):
        """获取交易报表
        
        Args:
            filters: 过滤条件 (dict)
            page: 页码
            per_page: 每页记录�?
            
        Returns:
            dict: 包含交易列表和分页信息的字典
        """
        filters = filters or {}
        query = Transaction.query
        
        # 应用过滤条件
        if 'start_date' in filters and 'end_date' in filters:
            query = query.filter(Transaction.created_at.between(
                filters['start_date'], filters['end_date']
            ))
        
        if 'transaction_type' in filters:
            query = query.filter(Transaction.transaction_type == filters['transaction_type'])
            
        if 'status' in filters:
            query = query.filter(Transaction.status == filters['status'])
            
        if 'project_id' in filters:
            query = query.filter(Transaction.project_id == filters['project_id'])
            
        if 'user_id' in filters:
            query = query.filter(Transaction.user_id == filters['user_id'])
            
        # 计算总数
        total = query.count()
        
        # 分页
        transactions = query.order_by(Transaction.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        # 转换为字典列�?
        transaction_list = [t.to_dict() for t in transactions]
        
        return {
            'transactions': transaction_list,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def get_payment_methods_report(start_date=None, end_date=None):
        """获取支付方式使用统计
        
        Args:
            start_date: 开始日�?(可�?
            end_date: 结束日期 (可�?
            
        Returns:
            list: 各支付方式的使用统计
        """
        # 设置默认时间范围为最�?0�?
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # 查询各支付方式的使用次数和金�?
        results = db.session.query(
                Transaction.payment_method,
                db.func.count(Transaction.id).label('count'),
                db.func.sum(Transaction.amount).label('total_amount')
            )\
            .filter(Transaction.created_at.between(start_date, end_date),
                   Transaction.transaction_type == TransactionType.DONATION.value,
                   Transaction.status == TransactionStatus.COMPLETED.value)\
            .group_by(Transaction.payment_method)\
            .all()
            
        # 计算总金�?
        total_amount = sum(float(r.total_amount or 0) for r in results)
        
        # 转换为字典列�?
        report = []
        for r in results:
            if r.payment_method:
                amount = float(r.total_amount or 0)
                percentage = (amount / total_amount * 100) if total_amount else 0
                
                report.append({
                    'payment_method': r.payment_method,
                    'count': r.count,
                    'total_amount': amount,
                    'percentage': round(percentage, 2)
                })
        
        return report 