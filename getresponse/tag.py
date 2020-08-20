class Tag(object):
    def __init__(self, *args, **kwargs):
        self.id = args[0]
        self.raw_data = None
        self.href = None
        self.name = None
        self.color = None

    def __repr__(self):
        return "<Tag(id='{}', name='{}'>".format(self.id, self.name)


class TagManager(object):
    def create(self, obj):
        if isinstance(obj, list):
            _list = []
            for item in obj:
                tag = self._create(**item)
                _list.append(tag)
            return _list

        tag = self._create(**obj)
        return tag

    @staticmethod
    def none_to_false(value):
        return False if value is None else value

    def _create(self, *args, **kwargs):
        tag = Tag(kwargs['tagId'])
        tag.raw_data = {'args': args if args else None,
                                 'kwargs': kwargs if kwargs else None}
        if 'href' in kwargs:
            tag.href = self.none_to_false(kwargs['href'])
        if 'name' in kwargs:
            tag.name = self.none_to_false(kwargs['name'])
        if 'color' in kwargs:
            tag.color = self.none_to_false(kwargs['color'])
       
        return tag
