from django.db import models

# Create your models here.
class UserProfile(models.Model):
    user_id = models.CharField(max_length=50, unique=True, verbose_name="用户ID")
    preferred_categories = models.JSONField(default=list, verbose_name="偏好类别")  # 如 ["手机", "耳机"]
    price_preference = models.CharField(max_length=50, blank=True, null=True, verbose_name="价格区间偏好")  # 如 "2000-4000"
    update_time = models.DateTimeField(auto_now=True, verbose_name="画像更新时间")

    class Meta:
        db_table = 'user_profile'
        verbose_name = "用户画像"
        verbose_name_plural = "用户画像库"

    def __str__(self):
        return f"用户 {self.user_id} 画像"