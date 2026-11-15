from reference_types import fields_of


class Reference:
    def __init__(self, id, user_id, entry_type, cite_key, fields):
        self.id = id
        self.user_id = user_id
        self.entry_type = entry_type
        self.cite_key = cite_key
        # field name -> value, contains only the fields that have a value
        self.fields = {
            name: fields[name]
            for name in fields_of(entry_type)
            if fields.get(name)
        }

    def __getattr__(self, name):
        # reference.author, reference.title, ...; None when the field is empty
        if name == "fields":
            raise AttributeError(name)
        return self.fields.get(name)
