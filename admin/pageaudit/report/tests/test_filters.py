from django.test import TestCase

from django.contrib.auth.models import User

from ..models import *

class TestUrlFilters(TestCase):

    def setUp(self):
        """
        create some urls and some filters
        """
        superuser = User(
            first_name='super',
            is_staff=True,
            is_superuser=True,
            last_name='User',
            username='superuser',
        )
        superuser.set_password('password!')
        superuser.save()

        urls = [
            'https://ibm.com/foo',
            'https://ibm.com/bar/baz/biff',
            'https://ibm.com/bar/baz/#w00t',
        ]

        url_arr = []

        for url in urls:
            url_arr.append(
                Url.objects.create(
                    created_by=superuser,
                    edited_by=superuser,
                    url=url
                )
            )

        # make 3 UrlFilters
        filters = ['foo', 'bar', 'foo or w00t']
        filter_arr = []

        for filter in filters:
            filter_arr.append(
                UrlFilter.objects.create(
                    name='%s filter' % filter,
                    description='%s filter description' % filter,
                    slug='%s-filter' % filter,
                    mode='AND' if 'or' not in filter else 'OR'
                )
            )

        for filter in filters:
            if filter == 'foo':
                UrlFilterPart.objects.create(
                    prop='path_segment',
                    filter_val=filter,
                    url_filter=filter_arr[0]
                )
            elif filter == 'bar':
                UrlFilterPart.objects.create(
                    prop='path_segment',
                    filter_val='baz',
                    filter_path_index=1,
                    url_filter=filter_arr[1]
                )
            elif filter == 'foo or w00t':
                UrlFilterPart.objects.create(
                    prop='hash',
                    filter_val='w00t',
                    url_filter=filter_arr[2]
                )
                UrlFilterPart.objects.create(
                    prop='path_segment',
                    filter_val='foo',
                    url_filter=filter_arr[2]
                )

    def test_UrlFilters(self):
        # import ipdb; ipdb.set_trace()
        foo = UrlFilter.objects.get(name='foo filter')
        # import ipdb; ipdb.set_trace()
        urls = foo.run_query()

        self.assertEqual(urls[0].url, 'https://ibm.com/foo')

        bar = UrlFilter.objects.get(name='bar filter')
        urls = bar.run_query()

        self.assertEqual(urls[0].url, 'https://ibm.com/bar/baz/#w00t')

        foo_or_woot = UrlFilter.objects.get(name='foo or w00t filter')
        urls = foo_or_woot.run_query()

        self.assertEqual(urls[0].url, 'https://ibm.com/bar/baz/#w00t')
        self.assertEqual(urls[1].url, 'https://ibm.com/foo')
        self.assertEqual(len(urls), 2)
