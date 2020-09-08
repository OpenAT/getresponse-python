import logging
import requests
from getresponse.enums import HttpMethod, ObjType
from .account import AccountManager
from .campaign import CampaignManager
from .contact import ContactManager
from .contact import Contact
from .custom_field import CustomFieldManager
from .tag import TagManager
from .excs import UniquePropertyError, NotFoundError, ValidationError, ForbiddenError, RelatedRecordNotFoundError

logger = logging.getLogger(__name__)


class GetResponse(object):
    API_BASE_URL = 'https://api.getresponse.com/v3'

    def __init__(self, api_key, timeout=8):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.account_manager = AccountManager()
        self.campaign_manager = CampaignManager()
        self.contact_manager = ContactManager(self.campaign_manager)
        self.custom_field_manager = CustomFieldManager()
        self.tag_manager = TagManager()

        self.session.headers.update({
            'X-Auth-Token': 'api-key {}'.format(self.api_key),
            'Content-Type': 'application/json'
        })

    def accounts(self, params=None):
        """Retrieves account information

        Args:
            params:
                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

        Examples:
            accounts({"fields": "firstName, lastName"})

        Returns:
            object: Account
        """
        return self._request('/accounts', ObjType.ACCOUNT, payload=params)

    def ping(self):
        """Checks if API Key is working

        Returns:
            bool: True for success, False otherwise
        """
        return True if self.accounts() else False

    def get_campaigns(self, params=None):
        """Retrieve campaigns information

        Args:
            params:
                query: Used to search only resources that meets criteria.
                You can specify multiple parameters, then it uses AND logic.

                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

                sort: Enable sorting using specified field (set as a key) and order (set as a value).
                You can specify multiple fields to sort by.

                page: Specify which page of results return.

                perPage: Specify how many results per page should be returned

        Examples:
            get_campaigns({"query": {"name": "XYZ"}})

        Returns:
            list: Campaign
        """
        return self._request('/campaigns', ObjType.CAMPAIGN, payload=params)

    def get_campaign(self, campaign_id, params=None):
        """Retrieves campaign information  

        Args:
            campaign_id: ID of the campaign

            params:
                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

        Returns:
            object: Campaign
        """
        return self._request('/campaigns/{}'.format(campaign_id), ObjType.CAMPAIGN, payload=params)

    def create_campaign(self, body):
        """Creates a campaign

        Args:
            body: data of the campaign

        Examples:
            create_campaign({"name": "XYZ"})

        Returns:
            object: Campaign
        """
        return self._request('/campaigns', ObjType.CAMPAIGN, HttpMethod.POST, body)

    def update_campaign(self, campaign_id, body):
        """Updates a campaign

        Args:
            campaign_id: ID of the campaign

            body: data of the campaign

        Examples:
            create_campaign("123", {"name": "XYZ"})

        Returns:
            object: Campaign
        """
        return self._request('/campaigns/{}'.format(campaign_id), ObjType.CAMPAIGN, HttpMethod.POST, body)

    def get_campaign_contacts(self, campaign_id, params=None):
        """Retrieve contacts from a campaign

        Args:
            campaign_id: ID of the campaign

            params:
                query: Used to search only resources that meets criteria.
                You can specify multiple parameters, then it uses AND logic.

                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

                sort: Enable sorting using specified field (set as a key) and order (set as a value).
                You can specify multiple fields to sort by.

                page: Specify which page of results return.

                perPage: Specify how many results per page should be returned

        Examples:
            get_campaign_contacts("123", {"query": {"name": "XYZ"}})

        Returns:
            list: Contact
        """
        return self._request('/campaigns/{}/contacts'.format(campaign_id), ObjType.CONTACT)

    def get_contacts(self, params=None):
        """Retrieve contacts from all campaigns

        Args:
            params:
                query: Used to search only resources that meets criteria.
                You can specify multiple parameters, then it uses AND logic.

                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

                sort: Enable sorting using specified field (set as a key) and order (set as a value).
                You can specify multiple fields to sort by.

                page: Specify which page of results return.

                perPage: Specify how many results per page should be returned

                additionalFlags: Additional flags parameter with value 'exactMatch' will search contacts
                with exact value of email and name provided in query string. Without that flag matching
                is done via standard 'like' comparison, what could be sometimes slow.

        Examples:
            get_contacts({"query[name]": "XYZ"})

        Returns:
            list: Contact
        """
        return self._request('/contacts', ObjType.CONTACT, payload=params)

    def get_all_contacts(self, campaign_ids=None, name=None, email=None, custom_fields=None,
                         subscriber_types=None):
        """ Convenince function to get/search for all contacts no matter what subscribersType they are.

        GetResponse will only return contacts of subscribersType "subscribed". To really get all contacts linked to
        a campaign you need to do contact searches for every subscribersType. This function eases the process of 
        creating a contact search request for every subscribersType.

        I also simplyfies the search for contacts with a specific name or email:
        E.g. get_all_contacts(name=('contains', 'Max') email='max@mustermann.com') will return all contacts for
        all campaigns and subscriberTypes where the email is 'max@mustermann.com' and the name contains 'Max'

        ATTENTION: !!! All search conditions will be combined as "AND" !!!

        :param campaign_ids: list
        :param name: tuple or string
            tuple format: (operator, value)
        :param email: tuple or string
            tuple format: (operator, value)
        :param custom_fields: list
            format: [(custom_field_id, operator, value)]

        :return: list
            returns a list with contact objects
        """
        subscriber_types = Contact.SUBSCRIBER_TYPES if not subscriber_types else subscriber_types
        _allowed_operators = ('is', 'is_not', 'contains', 'not_contains', 'starts', 'ends', 'not_starts', 'not_ends')

        # Search in all campaings
        if not campaign_ids:
            all_campaigns = self.get_campaigns({})
            campaign_ids = [c.id for c in all_campaigns]
        all_contacts = list()

        # Add search conditions
        conditions = []
        if name:
            if isinstance(name, basestring):
                operator, value = ('is', name)
            else:
                operator, value = name
            assert operator in _allowed_operators, "operator must be in %s" % _allowed_operators
            conditions.append({
                'conditionType': 'name',
                'operatorType': 'string_operator',
                'operator': operator,
                'value': value,
            })
        if email:
            if isinstance(email, basestring):
                operator, value = ('is', email)
            else:
                operator, value = email
            assert operator in _allowed_operators, "operator must be in %s" % _allowed_operators
            conditions.append({
                'conditionType': 'email',
                'operatorType': 'string_operator',
                'operator': operator,
                'value': value,
            })
        if custom_fields:
            custom_field_operators = _allowed_operators + ('assigned', 'not_assigned')
            for field_search in custom_fields:
                custom_field_id, operator, value = field_search
                assert operator in custom_field_operators, "operator must be in %s" % custom_field_operators
                cf_condition = {
                    'conditionType': 'custom',
                    'scope': custom_field_id,
                    'operatorType': 'string_operator_list',
                    'operator': operator,
                }
                if operator not in ('assigned', 'not_assigned'):
                    cf_condition['value'] = value
                conditions.append(cf_condition)

        # Search for the contacts (for any given subscriber_type)
        for subscriber_type in subscriber_types:
            contacts = self.search_contacts({
                "subscribersType": [
                    subscriber_type
                ],
                "sectionLogicOperator": "or",
                "section": [
                    {
                        "campaignIdsList": campaign_ids,
                        "logicOperator": "and",
                        "subscriberCycle": [
                            "receiving_autoresponder",
                            "not_receiving_autoresponder"
                        ],
                        "subscriptionDate": "all_time",
                        "conditions": conditions
                    }
                ]
            })
            all_contacts.extend(contacts)

        # Return a list with contact objects
        return all_contacts

    def get_contact(self, contact_id, params=None):
        """Retrieves contact information

        Args:
            contact_id: ID of the contact

            params:
                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

        Examples:
            get_contacts({"fields": "name, email"})

        Returns:
            object: Contact
        """
        return self._request('/contacts/{}'.format(contact_id), ObjType.CONTACT, payload=params)

    def create_contact(self, body):
        """Creates a contact

        Args:
            body: data of the contact

        Examples:
            create_contact({"email": "XYZ", "campaign": {"campaign_id": "XYZ"}})

        Returns:
            bool: True for success, False otherwise
        """
        return self._request('/contacts', ObjType.CONTACT, HttpMethod.POST, body)

    def update_contact(self, contact_id, body):
        """Updates a contact

        Args:
            contact_id: ID of the contact

            body: data of the contact

        Examples:
            update_contact("123", {"name": "XYZ"})

        Returns:
            object: Contact
        """
        return self._request('/contacts/{}'.format(contact_id), ObjType.CONTACT, HttpMethod.POST, body)

    def upsert_contact_custom_fields(self, contact_id, body):
        """Upsert (add or update) the custom fields of a contact. This method doesn't remove (unassign) custom fields.

        Args:
            contact_id: ID of the contact

            body: 'customFieldValues' dict with list of dicts

        Examples:
            upsert_contact_custom_fields("xyv3s", {"customFieldValues": [{"customFieldId": "kL6Nh","value": ["18-35"]}]})

        Returns:
            list: data from request answer
        """
        return self._request('/contacts/{}/custom-fields'.format(contact_id), None, HttpMethod.POST, body)

    def upsert_contact_tags(self, contact_id, body):
        """Upsert (add or update) the tags of a contact. This method doesn't remove (unassign) tags.

        Args:
            contact_id: ID of the contact

            body: 'tags' dict with list of dicts

        Examples:
            upsert_contact_tags("xyv3s", {"tags": [{"tagId": "m7E2"}]})

        Returns:
            list: data from request answer
        """
        return self._request('/contacts/{}/tags'.format(contact_id), None, HttpMethod.POST, body)

    def delete_contact(self, contact_id, params=None):
        """Deletes a contact

        Args:
            contact_id: ID of the contact

            params:
                messageId: ID of message

                ipAddress: User unsubscribe IP address

        Examples:
            delete_contact("123", {"messageId": "XYZ"})

        Returns:
            bool: True for success, False otherwise
        """
        return self._request('/contacts/{}'.format(contact_id), ObjType.CONTACT, HttpMethod.DELETE, payload=params)

    def get_custom_fields(self, params=None):
        """Retrieve custom fields for contacts

                Args:
                    params:
                        fields: List of fields that should be returned. Id is always returned.
                        Fields should be separated by comma

                        sort: Enable sorting using specified field (set as a key) and order (set as a value).
                        You can specify multiple fields to sort by.

                        page: Specify which page of results return.

                        perPage: Specify how many results per page should be returned
                Examples:
                    get_custom_fields({"fields": "name, fieldType"})

                Returns:
                    list: CustomField
                """
        return self._request('/custom-fields', ObjType.CUSTOM_FIELD, payload=params)

    def get_custom_field(self, custom_field_id, params=None):
        """Retrieve a custom field definition (for contacts)

                Args:
                    params:
                        fields: List of fields that should be returned. Id is always returned.
                        Fields should be separated by comma

                        sort: Enable sorting using specified field (set as a key) and order (set as a value).
                        You can specify multiple fields to sort by.

                        page: Specify which page of results return.

                        perPage: Specify how many results per page should be returned
                Examples:
                    get_custom_fields({"fields": "name, fieldType"})

                Returns:
                    list: CustomField
                """
        return self._request('/custom-fields/{}'.format(custom_field_id), ObjType.CUSTOM_FIELD, payload=params)

    def create_custom_field(self, body):
        """Creates a custom field definition

        Args:
            body: data of the custom field

        Examples:
            create_custom_field({})

        Returns:
            bool: True for success, False otherwise
        """
        return self._request('/custom-fields', ObjType.CUSTOM_FIELD, HttpMethod.POST, body)

    def update_custom_field(self, custom_field_id, body):
        """ TODO: Update a custom field definition

        :param custom_field_id:
        :param body:

        Returns:
            object: Custom Field
        """
        return self._request('/custom-fields/{}'.format(custom_field_id), ObjType.CUSTOM_FIELD, HttpMethod.POST, body)

    def delete_custom_field(self, custom_field_id):
        """Deletes a custom field definition

        Args:
            custom_field_id: ID of the custom field

        Examples:
            delete_custom_field("vy32424s")

        Returns:
            bool: True for success, False otherwise
        """
        return self._request('/custom-fields/{}'.format(custom_field_id), ObjType.CUSTOM_FIELD, HttpMethod.DELETE)



    # TODO: TAGS STUFF!!!
    # -------------------
    def get_tags(self, params=None):
        """ Retrieve list of tags

        Args:
            params:
                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

                sort: Enable sorting using specified field (set as a key) and order (set as a value).
                You can specify multiple fields to sort by.

                page: Specify which page of results return.

                perPage: Specify how many results per page should be returned
        Examples:
            get_tags({"fields": "name, fieldType"})

        Returns:
            list: Tags
        """
        return self._request('/tags', ObjType.TAG, payload=params)

    def get_tag(self, tag_id, params=None):
        """ Retrieve a tag definition

        Args:
            params:
                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

                sort: Enable sorting using specified field (set as a key) and order (set as a value).
                You can specify multiple fields to sort by.

                page: Specify which page of results return.

                perPage: Specify how many results per page should be returned
        Examples:
            get_tag('vBd5', params={"fields": "name, fieldType"})

        Returns:
            list: CustomField
        """
        return self._request('/tags/{}'.format(tag_id), ObjType.TAG, payload=params)

    def create_tag(self, body):
        """Creates a tag definition

        Args:
            body: data of the tag

        Examples:
            create_tag({'name': 'My_Tag'})

        Returns:
            bool: True for success, False otherwise
        """
        return self._request('/tags', ObjType.TAG, HttpMethod.POST, body)

    def update_tag(self, tag_id, body):
        """ Update a tag definition

        :param tag_id:
        :param body:

        Returns:
            object: Tag
        """
        return self._request('/tags/{}'.format(tag_id), ObjType.TAG, HttpMethod.POST, body)

    def delete_tag(self, tag_id):
        """Deletes a tag definition

        Args:
            custom_field_id: ID of the custom field

        Examples:
            delete_tag("vy32424s")

        Returns:
            bool: True for success, False otherwise
        """
        return self._request('/tags/{}'.format(tag_id), ObjType.TAG, HttpMethod.DELETE)
    # -------------------



    def get_rss_newsletter(self, rss_newsletter_id):
        return NotImplementedError

    def send_newsletter(self):
        return NotImplementedError

    def send_draft_newsletter(self):
        return NotImplementedError

    def search_contacts(self, body):
        """Search for contacts without storing the contact search (segment)

        Args:
            params: payload of the search

        Examples:
            search_contacts({
                                "subscribersType": [
                                    "subscribed"
                                ],
                                "sectionLogicOperator": "or",
                                "section": [
                                    {
                                        "campaignIdsList": [
                                            "V"
                                        ],
                                        "logicOperator": "or",
                                        "subscriberCycle": [
                                            "receiving_autoresponder",
                                            "not_receiving_autoresponder"
                                        ],
                                        "subscriptionDate": "all_time",
                                        "conditions": [
                                            {
                                                "conditionType": "email",
                                                "operatorType": "string_operator",
                                                "operator": "is",
                                                "value": "someEmail"
                                            },
                                            {
                                                "conditionType": "name",
                                                "operatorType": "string_operator",
                                                "operator": "not_contains",
                                                "value": "someName"
                                            },
                                            {
                                                "conditionType": "geo",
                                                "operatorType": "string_operator",
                                                "operator": "is_not",
                                                "value": "dsaDa",
                                                "scope": "country"
                                            }
                                        ]
                                    }
                                ]
                            })

        Returns:
            list: Contact
        """
        return self._request('/search-contacts/contacts', ObjType.CONTACT, HttpMethod.POST, body)

    def get_contacts_search(self):
        return NotImplementedError

    def add_contacts_search(self):
        return NotImplementedError

    def delete_contacts_search(self):
        return NotImplementedError

    def get_contact_activities(self):
        return NotImplementedError

    def get_webforms(self):
        return NotImplementedError

    def get_webform(self):
        return NotImplementedError

    def get_forms(self):
        return NotImplementedError

    def get_form(self):
        return NotImplementedError

    def get_billing_info(self):
        return NotImplementedError

    def _request(self, api_method, obj_type, http_method=HttpMethod.GET, body=None, payload=None):
        if http_method == HttpMethod.GET:
            logger.debug("url: %s, payload: %s" % (self.API_BASE_URL + api_method, payload))
            response = self.session.get(
                self.API_BASE_URL + api_method, params=payload, timeout=self.timeout)
            logger.debug("\"%s %s\" %s", http_method.name, response.url, response.status_code)
            # 200'er range = request OK !
            # ATTENTION: !!NOT!! in
            if response.status_code not in (200, 201, 202, 203, 204, 205, 206, 207, 208, 226):
                logger.error('%s\n%s' % (response.text, response.request))
                error = response.json()
                error_msg = error['message'] + u"\n" + str(error)
                if error['code'] == 1000:
                    raise ValidationError(error_msg, response=error)
                if error['code'] == 1001:
                    raise RelatedRecordNotFoundError(error_msg, response=error)
                if error['code'] == 1013:
                    raise NotFoundError(error_msg, response=error)
                if error['code'] == 1002:
                    raise ForbiddenError(error_msg, response=error)
                if error['code'] == 1008:
                    raise UniquePropertyError(error_msg, response=error)
                raise Exception(error_msg)
            if response.status_code == 202:
                logger.warning("Resource not ready in GetResponse! Object is not ready yet (still in creation/update)")
                return True
            return self._create_obj(obj_type, response.json(), request_body=body, request_payload=payload)

        if http_method == HttpMethod.POST:
            response = self.session.post(
                self.API_BASE_URL + api_method, json=body, params=payload, timeout=self.timeout)
            logger.debug("\"%s %s\" %s", http_method.name, response.url, response.status_code)
            # https://apidocs.getresponse.com/v3/errors
            # 200'er range = request OK !
            # ATTENTION: !!NOT!! in
            if response.status_code not in (200, 201, 202, 203, 204, 205, 206, 207, 208, 226):
                logger.error('%s\n%s' % (response.text, response.request))
                error = response.json()
                error_msg = error['message']+u"\n"+str(error)
                if error['code'] == 1000:
                    raise ValidationError(error_msg, response=error)
                if error['code'] == 1001:
                    raise RelatedRecordNotFoundError(error_msg, response=error)
                if error['code'] == 1013:
                    raise NotFoundError(error_msg, response=error)
                if error['code'] == 1002:
                    raise ForbiddenError(error_msg, response=error)
                if error['code'] == 1008:
                    raise UniquePropertyError(error_msg, response=error)
                raise Exception(error_msg)
            if response.status_code == 202:
                # Object is not ready yet (still in creation/update)
                logger.warning("Resource not ready in GetResponse! Object is not ready yet (still in creation/update)")
                return True
            return self._create_obj(obj_type, response.json(), request_body=body, request_payload=payload)

        if http_method == HttpMethod.DELETE:
            response = self.session.delete(
                self.API_BASE_URL + api_method, params=payload, timeout=self.timeout)
            logger.debug("\"%s %s\" %s", http_method.name, response.url, response.status_code)
            if response.status_code == 204:
                # Respuesta exitosa para un objeto que no se borra inmediatamente.
                return True
            return None

    def _create_obj(self, obj_type, data, request_body=None, request_payload=None):
        if obj_type == ObjType.ACCOUNT:
            obj = self.account_manager.create(data)
        elif obj_type == ObjType.CAMPAIGN:
            obj = self.campaign_manager.create(data)
        elif obj_type == ObjType.CONTACT:
            obj = self.contact_manager.create(data, request_body=request_body, request_payload=request_payload)
        elif obj_type == ObjType.CUSTOM_FIELD:
            obj = self.custom_field_manager.create(data)
        elif obj_type == ObjType.TAG:
            obj = self.tag_manager.create(data)
        else:
            return data
        return obj


class GetResponseEnterprise(GetResponse):
    def __init__(self, api_key, api_domain, api_base_url='https://api3.getresponse360.com/v3', **kwargs):
        #super().__init__(api_key, **kwargs)
        super(GetResponseEnterprise, self).__init__(api_key, **kwargs)
        self.API_BASE_URL = api_base_url
        self.session.headers.update({'X-Domain': api_domain})
