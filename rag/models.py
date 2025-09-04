from django.db import models

# Create your models here.
class ProductKnowledge(models.Model):
    product = models.ForeignKey('product.Products', on_delete=models.CASCADE, related_name='knowledge', verbose_name="关联商品")
    attribute = models.CharField(max_length=100, verbose_name="属性名")  # 如“是否支持无线充电”
    value = models.TextField(verbose_name="属性值")  # 如“支持15W无线充电”
    source_text = models.TextField(verbose_name="原文来源", blank=True, null=True)  # 原始说明文档片段
    embedding_vector = models.BinaryField(blank=True, null=True, verbose_name="向量表示")  # 可选：存储向量化结果

    class Meta:
        db_table = 'product_knowledge'
        verbose_name = "商品知识"
        verbose_name_plural = "商品知识库"

    def __str__(self):
        return f"{self.product.name} - {self.attribute}"