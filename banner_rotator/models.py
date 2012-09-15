try:
    from hashlib import md5
except ImportError:
    from md5 import md5
from time import time
from django.utils.translation import ugettext_lazy as _
from django.db import models
from filebrowser.fields import FileBrowseField
from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator
from banner_rotator.managers import BannerManager

_('Banner_Rotator') # app name translation for clever django-grappelli admin templates

class Campaign(models.Model):
    name = models.CharField(_('name'), max_length=255)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')

    def __unicode__(self):
        return self.name


class Place(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'))
    width = models.SmallIntegerField(_('width'), blank=True, null=True, default=None)
    height = models.SmallIntegerField(_('height'), blank=True, null=True, default=None)

    class Meta:
        unique_together = ('slug',)
        verbose_name = _('place')
        verbose_name_plural = _('places')

    def __unicode__(self):
        size_str = self.size_str()
        return '%s (%s)' % (self.name, size_str) if size_str else self.name

    def size_str(self):
        if self.width and self.height:
            return '%sx%s' % (self.width, self.height)
        elif self.width:
            return '%sxX' % self.width
        elif self.height:
            return 'Xx%s' % self.height
        else:
            return ''
    size_str.short_description = _('Size')


class Banner(models.Model):
    URL_TARGET_CHOICES = (
        ('_self', _('current page')),
        ('_blank', _('blank page')),
    )

    campaign = models.ForeignKey(Campaign, verbose_name=_('campaign'), blank=True, null=True, default=None,
        related_name="banners", db_index=True)

    name = models.CharField(_('name'), max_length=255)
    alt = models.CharField(_('image alternative text (alt)'), max_length=255, blank=True, default='')

    url = models.URLField(_('URL'))
    url_target = models.CharField(_('url target'), max_length=10, choices=URL_TARGET_CHOICES, default='')

    views = models.IntegerField(_('views'), default=0)
    clicks = models.IntegerField(_('clicks'), default=0)
    max_views = models.IntegerField(_('max views'), default=0)
    max_clicks = models.IntegerField(_('max clicks'), default=0)

    weight = models.IntegerField(_('weight'), help_text=_("A banner with weight set to 10 will display 10 times more often that one with a weight set to 1."),
        choices=[[i, i] for i in range(1, 11)], default=5)

#    file = models.FileField(_('File'), upload_to=get_banner_upload_to)
    file = FileBrowseField(verbose_name=_('file'), max_length=1000)
    file_hover = FileBrowseField(verbose_name=_('hover file'), max_length=1000, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    start_at = models.DateTimeField(_('start displaying at'), blank=True, null=True, default=None)
    finish_at = models.DateTimeField(_('finish displaying at'), blank=True, null=True, default=None)

    is_active = models.BooleanField(_('Is active'), default=True)

    places = models.ManyToManyField(Place, verbose_name=_('place'), related_name="banners", db_index=True)

    objects = BannerManager()

    class Meta:
        verbose_name = _('banner')
        verbose_name_plural = _('banners')

    def __unicode__(self):
        return self.name

    def is_swf(self):
        return self.file.name.lower().endswith("swf")

    def view(self):
        self.views = models.F('views') + 1
        self.save()
        return ''

    def click(self, request):
        self.clicks = models.F('clicks') + 1
        self.save()

        place = None
        if 'place' in request.GET:
            place = request.GET['place']
        elif 'place_slug' in request.GET:
            place = request.GET['place_slug']

        try:
            place_qs = Place.objects
            if 'place' in request.GET:
                place = place_qs.get(id=request.GET['place'])
            elif 'place_slug' in request.GET:
                place = place_qs.get(slug=request.GET['place_slug'])
        except Place.DoesNotExist:
            place = None

        click = {
            'banner': self,
            'place': place,
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'referrer': request.META.get('HTTP_REFERER'),
        }

        if request.user.is_authenticated():
            click['user'] = request.user

        return Click.objects.create(**click)

    @models.permalink
    def get_absolute_url(self):
        return 'banner_click', (), {'banner_id': self.pk}

    def admin_clicks_str(self):
        if self.max_clicks:
            return '%s / %s' % (self.clicks, self.max_clicks)
        return '%s' % self.clicks
    admin_clicks_str.short_description = _('clicks')

    def admin_views_str(self):
        if self.max_views:
            return '%s / %s' % (self.views, self.max_views)
        return '%s' % self.views
    admin_views_str.short_description = _('views')


class Click(models.Model):
    banner = models.ForeignKey(Banner, related_name="clicks_list")
    place = models.ForeignKey(Place, related_name="clicks_list", null=True, default=None)
    user = models.ForeignKey(User, null=True, blank=True, related_name="banner_clicks")
    datetime = models.DateTimeField("Clicked at", auto_now_add=True)
    ip = models.IPAddressField(null=True, blank=True)
    user_agent = models.TextField(validators=[MaxLengthValidator(1000)], null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)