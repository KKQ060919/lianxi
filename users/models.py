from django.db import models

# Create your models here.
class UserBehavior(models.Model):
    user_id = models.CharField(max_length=50, verbose_name="用户ID")
    product = models.ForeignKey('product.Products', on_delete=models.CASCADE, verbose_name="浏览商品")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="浏览时间")
    action_type = models.CharField(max_length=20, default="view", verbose_name="行为类型")  # view, click, favorite 等

    class Meta:
        db_table = 'user_behavior'
        indexes = [
            models.Index(fields=['user_id', '-viewed_at']),
        ]
        verbose_name = "用户行为日志"
        verbose_name_plural = "用户行为日志"

    def __str__(self):
        return f"{self.user_id} 浏览了 {self.product.name}"