from django.test import TestCase
from django_any import any_model
from .models import *
from django.core.urlresolvers import reverse

class ClickBannerTestCase(TestCase):

    def setUp(self):
        pass

    def test_banner_click_behaviour(self):
        banner = any_model(Banner,
            url='https://github.com/gbezyuk',
            file='no_matter', file_hover='no_matter',
            max_clicks=0, max_views=0, views=0, clicks=0)
        self.assertEqual(banner.clicks, 0)
        self.assertEqual(banner.views, 0)
        resp = self.client.get(reverse('banner_click', kwargs={'banner_id': banner.id}))
        self.assertEqual(resp.status_code, 302, "Banner click should redirect to its location")
        self.assertIn('Location: %s' % banner.url, str(resp))
        banner = Banner.objects.get(pk=banner.pk)
        self.assertEqual(banner.clicks, 1)
        self.assertEqual(banner.views, 0)