from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from umbrella.models import Umbrella


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email)
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password
        )
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('电子邮箱'), unique=True)
    school = models.CharField(_('学校'), max_length=150)
    pledge_money = models.FloatField(_('押金余额'), default=0.0)
    balance = models.FloatField(_('账户余额'), default=0.0)
    is_active = models.BooleanField(
        _('是否激活'),
        default=True,
        help_text=_(
            '将该选项设置为未激活则可认为该用户被删除'
        ),
    )
    date_joined = models.DateTimeField(_('加入时间'), default=timezone.now)

    @property
    def is_staff(self):
        return self.is_superuser

    objects = MyUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('用户信息')
        verbose_name_plural = verbose_name
        # abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return "<UserProfile: {}-{}>".format(self.email, self.school)


class UserLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='用户')
    time = models.DateTimeField('动作发生时间', auto_now_add=True)
    action = models.CharField('发生动作', max_length=10, choices=(
                                  ('1', '借伞'),
                                  ('2', '还伞'),
                                  ('3', '充值')))
    memo = models.TextField('备注', blank=True, null=True)

    def __str__(self):
        return "<UserLog: {}-{}>".format(self.user, self.action)

    class Meta:
        verbose_name = '用户日志'
        verbose_name_plural = verbose_name


class UserInventory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='用户')
    time = models.DateTimeField('动作发生时间', auto_now_add=True)
    umbrella = models.ForeignKey(Umbrella, on_delete=models.CASCADE, verbose_name='伞')

    def __str__(self):
        return "<UserInventory: {}-{}>".format(self.user, self.umbrella)

    class Meta:
        verbose_name = '用户物品栏'
        verbose_name_plural = verbose_name
