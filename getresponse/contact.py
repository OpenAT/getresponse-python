import datetime
import dateutil.parser

class Contact(object):
    SUBSCRIBER_TYPES  = ('subscribed', 'undelivered', 'removed', 'unconfirmed')

    def __init__(self, *args, **kwargs):
        self.id = args[0]
        self.raw_data = None
        self.href = None
        self.name = None
        self.email = None
        self.note = None
        self.day_of_cycle = None
        self.origin = None
        self.created_on = None
        self.changed_on = None
        self.campaign = None
        self.timezone = None
        self.ip_address = None
        self.activities = None
        self.scoring = None
        self.custom_field_values = None
        self.tags = None
        self.engagement_score = None

        # This is not returned by any /contact* route. We can assume that it is always 'subscribed' for the
        # /contact* routes since non "subscribed" contacts will NOT be returned by default. Contacts with a
        # subscribersType of ['undelivered', 'removed', 'unconfirmed'] can only be returend by a "search contacts" 
        # (segment) object. These search segments have the routes "/search-contacts*"
        self.subscribers_type = None

    def __repr__(self):
        return u"<Contact(id='{}', name='{}', email='{}'>".format(self.id, self.name, self.email).encode('utf-8')


class ContactManager(object):
    def __init__(self, *args, **kwargs):
        self.campaign_manager = args[0]

    def create(self, obj, request_body=None, request_payload=None):
        if isinstance(obj, list):
            _list = []
            for item in obj:
                contact = self._create(request_body=request_body, request_payload=request_payload, **item)
                _list.append(contact)
            return _list

        contact = self._create(**obj)
        return contact

    @staticmethod
    def none_to_false(value):
        return False if value is None else value

    def _create(self, request_body=None, request_payload=None, *args, **kwargs):

        contact = Contact(kwargs['contactId'])

        # raw_data
        contact.raw_data = {'args': args if args else None,
                            'kwargs': kwargs if kwargs else None}

        # subscribers_type
        # HINT: 'subscribersType' can/will only be used in /contact-search routes.
        if request_body and request_body.get('subscribersType'):
            contact.subscribers_type = request_body.get('subscribersType')[0]
        else:
            contact.subscribers_type = 'subscribed'
        assert contact.subscribers_type in Contact.SUBSCRIBER_TYPES, "subscribers_type is '%s' but must be in %s" % (
            contact.subscribers_type, str(Contact.SUBSCRIBER_TYPES)
        )

        if 'href' in kwargs:
            contact.href = self.none_to_false(kwargs['href'])
        if 'name' in kwargs:
            contact.name = self.none_to_false(kwargs['name'])
        if 'email' in kwargs:
            contact.email = self.none_to_false(kwargs['email'])
        if 'note' in kwargs:
            contact.note = self.none_to_false(kwargs['note'])
        if 'dayOfCycle' in kwargs:
            contact.day_of_cycle = self.none_to_false(kwargs['dayOfCycle'])
        if 'origin' in kwargs:
            contact.origin = self.none_to_false(kwargs['origin'])
        if 'createdOn' in kwargs:
            created_on = self.none_to_false(kwargs['createdOn'])
            if created_on:
                contact.created_on = dateutil.parser.parse(created_on)
        if 'changedOn' in kwargs:
            changed_on = self.none_to_false(kwargs['changedOn'])
            if changed_on:
                contact.changed_on = dateutil.parser.parse(changed_on)
        if 'campaign' in kwargs:
            campaign = self.campaign_manager.create(self.none_to_false(kwargs['campaign']))
            contact.campaign = campaign
        if 'timeZone' in kwargs:
            contact.timezone = self.none_to_false(kwargs['timeZone'])
        if 'ipAddress' in kwargs:
            contact.ip_address = self.none_to_false(kwargs['ipAddress'])
        if 'activities' in kwargs:
            contact.activities = self.none_to_false(kwargs['activities'])
        if 'scoring' in kwargs:
            contact.scoring = self.none_to_false(kwargs['scoring'])
        if 'customFieldValues' in kwargs:
            contact.custom_field_values = self.none_to_false(kwargs['customFieldValues'])
        if 'tags' in kwargs:
            contact.tags = self.none_to_false(kwargs['tags'])
        if 'engagementScore' in kwargs:
            contact.engagement_score = self.none_to_false(kwargs['engagementScore'])



        return contact
