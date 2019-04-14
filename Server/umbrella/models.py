import hashlib
from django.db import models


class Umbrella(models.Model):
    uid = models.CharField('UID', max_length=50, unique=True, null=False)  # 伞的读卡号
    color = models.CharField('颜色', max_length=20, blank=True, null=True)  # 颜色
    category = models.CharField('类型', max_length=20, choices=(
        ('折叠伞', '折叠伞'),
        ('长柄伞', '长柄伞'),
    ), blank=True, null=True)
    type = models.CharField('类别', max_length=20, choices=(
        ('雨伞', '雨伞'),
        ('太阳伞', '太阳伞'),
    ), blank=True, null=True)
    status = models.CharField('出借状态', max_length=20, choices=(
        ('1', '在架'),
        ('0', '借出'),
        ('2', '空闲'),
    ))

    def __str__(self):
        return "<Umbrella: {}-{}>".format(self.status, self.uid)

    class Meta:
        verbose_name = "伞信息"
        verbose_name_plural = verbose_name


class UmbrellaShelf(models.Model):
    loc_school = models.CharField('学校', max_length=150) # 在哪个学校
    loc_position = models.CharField('具体位置', max_length=500) # 具体位置
    capacity = models.IntegerField('容量', default=8)    #  伞架的容量，默认为8
    identify_code = models.CharField('验证码', max_length=256, default='CA4238A0B923820DCC509A6F75849B')

    def create_identify_code(self):
        hl = hashlib.md5()
        hl.update(str(self.pk).encode())
        return hl.hexdigest().upper()

    def __str__(self):
        return "<UmbrellaShelf: {}-{}>".format(self.loc_school, self.loc_position)

    class Meta:
        verbose_name = "伞架信息"
        verbose_name_plural = verbose_name


class UmbrellaShelf2Position(models.Model):
    umbrella_shelf = models.ForeignKey(UmbrellaShelf, on_delete=models.CASCADE, verbose_name='伞架')
    position = models.IntegerField('伞架位置')    # 哪个位置
    status = models.CharField(max_length=20, choices=(
        ('1', '有伞'),
        ('0', '没伞'),
    ))
    umbrella = models.ForeignKey(Umbrella, on_delete=models.SET_NULL, 
                                blank=True, null=True, verbose_name='雨伞')

    def __str__(self):
        return "<Position: {}-{}-{}>".format(self.umbrella_shelf, self.position, self.status)

    class Meta:
        verbose_name = "伞架位置信息"
        verbose_name_plural = verbose_name
