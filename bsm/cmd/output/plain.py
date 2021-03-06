def _format_dict(d):
    max_key_length = 0
    for k in d:
        key_length = len(str(k))
        if max_key_length < key_length:
            max_key_length = key_length
    return '\n'.join(['{0:{width}} : {1}'.format(k, v, width=max_key_length) for k, v in d.items()])


class Plain(object):
    def dump(self, value):
        if isinstance(value, (list, tuple)):
            return '\n'.join([str(v) for v in value])
        if isinstance(value, dict):
            return _format_dict(value)
        return str(value)
