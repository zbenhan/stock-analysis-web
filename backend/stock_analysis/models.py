from django.db import models

class SecurityInfo(models.Model):
    security_code = models.TextField(primary_key=True)
    security_name = models.TextField()
    listing_board = models.TextField()
    industry_name = models.TextField()

    class Meta:
        db_table = 'security_info'
        managed = False  # 使用现有表，不管理迁移

    def __str__(self):
        return f"{self.security_name} ({self.security_code})"

class ClosingPrice(models.Model):
    EntryID = models.TextField(primary_key=True)   # 声明主键
    security_code = models.TextField()
    total_share_capital = models.TextField()
    trade_date = models.TextField()
    closing_price = models.FloatField()

    class Meta:
        db_table = 'closing_price'
        managed = False
        # 原来 unique_together 可以保留，也可以去掉 不要主键
        unique_together = (('security_code', 'EntryID'),)

    def __str__(self):
        return f"{self.security_code} - {self.trade_date}"

class FinancialReport(models.Model):
    security_code = models.TextField()
    report_period = models.TextField()
    parent_equity_attributable = models.FloatField()
    net_profit_parent_chareholders = models.FloatField()

    class Meta:
        db_table = 'financial_report'
        managed = False
        unique_together = (('security_code', 'report_period'),)

    def __str__(self):
        return f"{self.security_code} - {self.report_period}"