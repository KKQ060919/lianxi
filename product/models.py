from django.db import models

# Create your models here.
class Products(models.Model):
    product_id = models.CharField(max_length=50, unique=True, verbose_name="商品ID")
    name = models.CharField(max_length=200, verbose_name="商品名称")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="价格")
    category = models.CharField(max_length=100, verbose_name="商品类别")
    brand = models.CharField(max_length=100, verbose_name="品牌")
    specifications = models.JSONField(verbose_name="规格参数", default=dict)  # 如颜色、内存等
    description = models.TextField(verbose_name="商品描述", blank=True, null=True)
    stock = models.IntegerField(verbose_name="库存")
    is_hot = models.BooleanField(default=False, verbose_name="是否热门")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'product'
        verbose_name = "商品"
        verbose_name_plural = "商品列表"

    def __str__(self):
        return self.name

