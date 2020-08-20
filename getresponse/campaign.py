import datetime
import dateutil.parser

def lazy_property(fn):
    '''Decorator that makes a property lazy-evaluated.
    '''
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property


class Campaign(object):
    def __init__(self, *args, **kwargs):
        self.id = args[0]
        self.raw_data = None
        self.href = None
        self.name = None
        self.language_code = None
        self.is_default = None
        self.created_on = None
        self.description = None
        self.confirmation = None
        self.profile = None
        self.postal = None
        self.opting_types = None
        self.subscription_notifications = None

    def __repr__(self):
        return "<Campaign(id='{}', name='{}', is_default='{}'>".format(self.id, self.name, self.is_default)




class CampaignManager(object):
    def create(self, obj):
        if isinstance(obj, list):
            _list = []
            for item in obj:
                campaign = self._create(**item)
                _list.append(campaign)
            return _list

        campaign = self._create(**obj)
        return campaign

    @staticmethod
    def none_to_false(value):
        return False if value is None else value

    def _create(self, *args, **kwargs):

        campaign = Campaign(kwargs['campaignId'])

        campaign.raw_data = {'args': args if args else None,
                             'kwargs': kwargs if kwargs else None}

        if 'href' in kwargs:
            campaign.href = self.none_to_false(kwargs['href'])
        if 'name' in kwargs:
            campaign.name = self.none_to_false(kwargs['name'])
        if 'languageCode' in kwargs:
            campaign.language_code = self.none_to_false(kwargs['languageCode'])
        if 'isDefault' in kwargs:
            campaign.is_default = self.none_to_false(kwargs['isDefault'])
        if 'createdOn' in kwargs:
            created_on = self.none_to_false(kwargs['createdOn'])
            if created_on:
                # campaign.created_on = datetime.datetime.strptime(created_on, '%Y-%m-%dT%H:%M:%S%z')
                campaign.created_on = dateutil.parser.parse(created_on)
        if 'description' in kwargs:
            campaign.description = self.none_to_false(kwargs['description'])
        if 'confirmation' in kwargs:
            campaign.confirmation = self.none_to_false(kwargs['confirmation'])
        if 'profile' in kwargs:
            campaign.profile = self.none_to_false(kwargs['profile'])
        if 'postal' in kwargs:
            campaign.postal = self.none_to_false(kwargs['postal'])
        if 'optinTypes' in kwargs:
            campaign.opting_types = self.none_to_false(kwargs['optinTypes'])
        if 'subscriptionNotifications' in kwargs:
            campaign.subscription_notifications = self.none_to_false(kwargs['subscriptionNotifications'])
        return campaign
