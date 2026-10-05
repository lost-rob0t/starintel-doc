"""Duplicate-safe raw readers for SDK-owned historical dataclass models.

Keep the historical decoder's options, hooks, and numeric representations. Only
the SDK's decorated classes are changed; dataclasses-json itself is untouched.
"""
from functools import wraps

from dataclasses_json import dataclass_json as _dataclass_json

from starintel_canonical.errors import ValidationError


def unique_object(pairs):
    """Reject repeated decoded names in one object before dict conversion."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError('duplicate_key', f'Duplicate JSON key: {key!r}')
        result[key] = value
    return result


@wraps(_dataclass_json)
def dataclass_json(_cls=None, **options):
    """Apply dataclasses-json and guard this SDK class's generated raw reader."""
    def decorate(cls):
        cls = _dataclass_json(cls, **options)
        original = cls.from_json.__func__

        @wraps(original)
        def from_json(model, *args, **kwargs):
            pairs_hook = kwargs.get('object_pairs_hook')
            object_hook = kwargs.get('object_hook')

            def checked_pairs(pairs):
                value = unique_object(pairs)
                # Match json.loads: object_pairs_hook takes precedence over
                # object_hook. Invoke caller callbacks exactly once per object.
                if pairs_hook is not None:
                    return pairs_hook(pairs)
                if object_hook is not None:
                    return object_hook(value)
                return value

            kwargs['object_pairs_hook'] = checked_pairs
            return original(model, *args, **kwargs)

        cls.from_json = classmethod(from_json)
        return cls

    return decorate if _cls is None else decorate(_cls)
