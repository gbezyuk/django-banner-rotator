from datetime import datetime
from random import random

from django.db import models


def pick(bias_list):
    """
    Takes a list similar to [(item1, item1_weight), (item2, item2_weight),]
        and item(n)_weight as the probability when calculating an item to choose
    """

    # All weights should add up to 1
    #   an items weight is equivalent to it's probability of being picked
    assert sum(i[1] for i in bias_list) == 1

    number = random()
    current = 0

    # With help from
    #   @link http://fr.w3support.net/index.php?db=so&id=479236
    for choice, bias in bias_list:
        current += bias
        if number <= current:
            return choice


class BannerManager(models.Manager):
    def biased_choice(self, place):
        now = datetime.now()

        # conditions verification:
        # - active and bounded to specified place
        # - display start time restriction passes
        # - display finish time restriction passes
        # - max_views restriction passes
        # - max_clicks restriction passes
        queryset = self.filter(is_active=True, places=place).\
                    filter(models.Q(start_at__isnull=True) | models.Q(start_at__lte=now)).\
                    filter(models.Q(finish_at__isnull=True) | models.Q(finish_at__gte=now)).\
                    filter(models.Q(max_views=0) | models.Q(max_views__gt=models.F('views'))).\
                    filter(models.Q(max_clicks=0) | models.Q(max_clicks__gt=models.F('clicks')))

        if not queryset.count():
            raise self.model.DoesNotExist

        calculations = queryset.aggregate(weight_sum=models.Sum('weight'))

        banners = queryset.extra(select={'bias': 'weight/%f' % calculations['weight_sum']})

        return pick([(b, b.bias) for b in banners])
