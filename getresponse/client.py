import logging
import requests
from copy import deepcopy
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

    def get_campaigns(self, per_page=None, page=None, params=None):
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
        local_params = deepcopy(params) if params else {}

        if per_page:
            assert 'perPage' not in local_params, "'perPage' was found in 'local_params' and in 'per_page'!"
            assert 0 < per_page <= 1000, "The maximum number of campaigns per page is 1000 the minimum is 1!"
            local_params['perPage'] = per_page
        elif 'perPage' in local_params:
            per_page = local_params['perPage']
        if per_page:
            per_page = int(per_page)
            local_params['perPage'] = per_page

        if page:
            assert 'page' not in local_params, "'page' was found in 'local_params' and in 'page'! Use one only!"
        elif 'page' in local_params:
            page = local_params['page']
        if page:
            page = int(page)

        # Get contacts paginated
        all_campaigns = list()
        paged_campaigns = True
        current_page = deepcopy(page) if page else 1
        paged_payload = deepcopy(local_params)
        while paged_campaigns and current_page:
            paged_payload['page'] = current_page
            paged_campaigns = self._request('/campaigns', ObjType.CAMPAIGN, payload=paged_payload)
            all_campaigns.extend(paged_campaigns)

            # Stop the while loop if 'page' is given
            if page:
                current_page = False
            # Move on to the next page if 'page' is not given
            else:
                current_page += 1

        return all_campaigns

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

    def get_contacts(self, params=None, per_page=None, page=None):
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
        local_params = deepcopy(params) if params else {}

        if per_page:
            assert 'perPage' not in local_params, "'perPage' was found in 'local_params' and in 'per_page'! Use one only!"
            assert 0 < per_page <= 1000, "The maximum number of contacts per page is 1000 the minimum is 1!"
            local_params['perPage'] = per_page
        elif 'perPage' in local_params:
            per_page = local_params['perPage']
        if per_page:
            per_page = int(per_page)
            local_params['perPage'] = per_page

        if page:
            assert 'page' not in local_params, "'page' was found in 'local_params' and in 'page'! Use one only!"
        elif 'page' in local_params:
            page = local_params['page']
        if page:
            page = int(page)

        all_contacts = list()

        # Get contacts paginated
        paged_contacts = True
        current_page = deepcopy(page) if page else 1
        paged_payload = deepcopy(local_params)
        while paged_contacts and current_page:
            paged_payload['page'] = current_page
            paged_contacts = self._request('/contacts', ObjType.CONTACT, payload=paged_payload)

            # Append the found contacts to the result
            all_contacts.extend(paged_contacts)

            # Stop the while loop if 'page' is given
            if page:
                current_page = False
            # Move on to the next page if 'page' is not given
            else:
                current_page += 1

        return all_contacts

    def get_all_contacts(self, campaign_ids=None, name=None, email=None, custom_fields=None,
                         subscriber_types=None, per_page=None, page=None, params=None):
        """ Convenince function to get/search for all contacts no matter what subscribersType they are.

        GetResponse will only return contacts of subscribersType "subscribed". To really get all contacts linked to
        a campaign you need to do contact searches for every subscribersType. This function eases the process of 
        creating a contact search request for every subscribersType.

        Example:  get_all_contacts(subscriber_types=['subscribed', 'unconfirmed'])

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

        # Search for all campaings if no campaing ids are given
        if not campaign_ids:
            all_campaigns = self.get_campaigns({})
            campaign_ids = [c.id for c in all_campaigns]

        # ADD SEARCH CONDITIONS
        # ---------------------
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

        # SEARCH FOR THE CONTACTS FOR ANY GIVEN SUBSCRIBER_TYPE
        # -----------------------------------------------------
        all_contacts = list()
        for subscriber_type in subscriber_types:

            body = {
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
            }

            # Paginated search for contacts of subscribers
            subscriber_type_contacts = self.search_contacts(body, per_page=per_page, page=page, params=params)
            all_contacts.extend(subscriber_type_contacts)

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

    def get_custom_fields(self, per_page=None, page=None, params=None):
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
        local_params = deepcopy(params) if params else {}

        if per_page:
            assert 'perPage' not in local_params, "'perPage' was found in 'local_params' and in 'per_page'!"
            assert 0 < per_page <= 1000, "The maximum number of custom fields per page is 1000 the minimum is 1!"
            local_params['perPage'] = per_page
        elif 'perPage' in local_params:
            per_page = local_params['perPage']
        if per_page:
            per_page = int(per_page)
            local_params['perPage'] = per_page

        if page:
            assert 'page' not in local_params, "'page' was found in 'local_params' and in 'page'! Use one only!"
        elif 'page' in local_params:
            page = local_params['page']
        if page:
            page = int(page)

        all_custom_fields = list()

        # Get custom fields paginated
        paged_custom_fields = True
        current_page = deepcopy(page) if page else 1
        paged_payload = deepcopy(local_params)
        while paged_custom_fields and current_page:
            paged_payload['page'] = current_page
            paged_custom_fields = self._request('/custom-fields', ObjType.CUSTOM_FIELD, payload=paged_payload)

            # Append the found contacts to the result
            all_custom_fields.extend(paged_custom_fields)

            # Stop the while loop if 'page' is given
            if page:
                current_page = False
            # Move on to the next page if 'page' is not given
            else:
                current_page += 1

        return all_custom_fields



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

    def get_tags(self, per_page=None, page=None, params=None):
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
        local_params = deepcopy(params) if params else {}

        if per_page:
            assert 'perPage' not in local_params, "'perPage' was found in 'local_params' and in 'per_page'!"
            assert 0 < per_page <= 1000, "The maximum number of tags per page is 1000 the minimum is 1!"
            local_params['perPage'] = per_page
        elif 'perPage' in local_params:
            per_page = local_params['perPage']
        if per_page:
            per_page = int(per_page)
            local_params['perPage'] = per_page

        if page:
            assert 'page' not in local_params, "'page' was found in 'local_params' and in 'page'! Use one only!"
        elif 'page' in local_params:
            page = local_params['page']
        if page:
            page = int(page)

        all_tags = list()

        # Get tags paginated
        paged_tags = True
        current_page = deepcopy(page) if page else 1
        paged_payload = deepcopy(local_params)
        while paged_tags and current_page:
            paged_payload['page'] = current_page
            paged_tags = self._request('/tags', ObjType.TAG, payload=paged_payload)

            # Append the found contacts to the result
            all_tags.extend(paged_tags)

            # Stop the while loop if 'page' is given
            if page:
                current_page = False
            # Move on to the next page if 'page' is not given
            else:
                current_page += 1

        return all_tags

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

    def search_contacts(self, body, per_page=100, page=None, params=None):
        """Search for contacts without storing the contact search (segment)

        Args:
            body: conditions for the search
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
                            },
                            params={'perPage': 50, 'page': 1})

        Options for params:
            query	hash	Used to search only resources that meet the criteria. You can specify multiple parameters. Then, the AND logic is applied. Available search parameters: name=*, createdOn[from]=Y-m-d, createdOn[to]=Y-m-d, i.e. ?query[name]=my+custom+filer&query[createdOn][from]=2018-04-01&query[createdOn][to]=2018-04-11
            fields	string	List of fields that should be returned. Id is always returned. Fields should be separated by comma. Available field names depends on request: name, createdOn, href. i.e.: ?fields=name,createdOn
            sort	hash	Enable sorting using specified field (set as a key) and order (set as a value). You can specify multiple fields to sort by. Available keys name=asc|desc and createdOn=asc|desc. i.e: ?sort[name]=desc&createdOn=asc
            page	integer	Specify which page of results should return.
            perPage	integer	Specify how many results per page should be returned. The maximum allowed number of results is 1000. Up to 8 conditions are allowed.

        Returns:
            list: Contact
        """
        local_params = deepcopy(params) if params else {}

        if per_page:
            assert 'perPage' not in local_params, "'perPage' was found in 'local_params' and in 'per_page'!"
            assert 0 < per_page <= 1000, "The maximum number of contacts per page is 1000 the minimum is 1!"
            local_params['perPage'] = per_page
        elif 'perPage' in local_params:
            per_page = local_params['perPage']
        if per_page:
            per_page = int(per_page)
            local_params['perPage'] = per_page

        if page:
            assert 'page' not in local_params, "'page' was found in 'local_params' and in 'page'! Use one only!"
        elif 'page' in local_params:
            page = local_params['page']
        if page:
            page = int(page)

        # Get contacts paginated
        all_contacts = list()
        paged_contacts = True
        current_page = deepcopy(page) if page else 1
        paged_payload = deepcopy(local_params)
        while paged_contacts and current_page:
            paged_payload['page'] = current_page
            paged_contacts = self._request('/search-contacts/contacts', ObjType.CONTACT, HttpMethod.POST,
                                           body=body, payload=paged_payload)
            all_contacts.extend(paged_contacts)

            # Stop the while loop if 'page' is given
            if page:
                current_page = False
            # Move on to the next page if 'page' is not given
            else:
                current_page += 1

        return all_contacts

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
