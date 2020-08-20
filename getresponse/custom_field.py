class CustomField(object):
    def __init__(self, *args, **kwargs):
        self.id = args[0]
        self.raw_data = None
        self.href = None
        self.name = None
        self.type = None
        self.value_type = None
        self.format = None
        self.field_type = None
        self.hidden = None
        self.values = None

    def __repr__(self):
        return "<CustomField(id='{}', name='{}'>".format(self.id, self.name)


class CustomFieldManager(object):
    def create(self, obj):
        if isinstance(obj, list):
            _list = []
            for item in obj:
                custom_field = self._create(**item)
                _list.append(custom_field)
            return _list

        custom_field = self._create(**obj)
        return custom_field

    @staticmethod
    def none_to_false(value):
        return False if value is None else value

    def _create(self, *args, **kwargs):
        custom_field = CustomField(kwargs['customFieldId'])
        custom_field.raw_data = {'args': args if args else None,
                                 'kwargs': kwargs if kwargs else None}
        if 'href' in kwargs:
            custom_field.href = self.none_to_false(kwargs['href'])
        if 'name' in kwargs:
            custom_field.name = self.none_to_false(kwargs['name'])
        if 'type' in kwargs:
            custom_field.type = self.none_to_false(kwargs['type'])
        if 'valueType' in kwargs:
            custom_field.value_type = self.none_to_false(kwargs['valueType'])
        if 'format' in kwargs:
            custom_field.format = self.none_to_false(kwargs['format'])
        if 'fieldType' in kwargs:
            custom_field.field_type = self.none_to_false(kwargs['fieldType'])
        if 'hidden' in kwargs:
            custom_field.hidden = self.none_to_false(kwargs['hidden'])
        if 'values' in kwargs:
            custom_field.values = self.none_to_false(kwargs['values'])
        return custom_field
