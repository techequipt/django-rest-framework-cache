from collections import defaultdict
from django.db.models import signals
from django.utils.module_loading import autodiscover_modules
from django.contrib.admin.utils import reverse_field_path

from .exceptions import AlreadyRegistered


class CacheRegistry:
    def __init__(self):
        self._registry = {}
        self._related_registry = defaultdict(list)

    def register(self, serializer, relations_to_track=[]):
        """Store the serializer and model on registry to that the cache can be
        cleaned whenever an object is changed or deleted.
        After the serializer is registered we must connect the signals that
        clear the instance cache.

        relations_to_track will allow you to designate further signals to trigger cache
        clearing. relations_to_track uses the django queryset relation__field method for resolving.
        """
        model = serializer.Meta.model

        if model not in self._registry:
            self._registry[model] = []

        if serializer in self._registry[model]:
            raise AlreadyRegistered(
                "Serializer {} is already registered".format(model.__name__)
            )

        self._registry[model].append(serializer)
        self.connect_signals(model)

        for relation_str in relations_to_track:
            related_model, lookup = reverse_field_path(model, relation_str)
            self._related_registry[related_model].append(lookup)
            self.connect_related_signals(related_model)

    def connect_signals(self, model):
        from .signals import clear_instance  # NOQA - Prevent circular import

        signals.post_save.connect(clear_instance, sender=model)
        signals.pre_delete.connect(clear_instance, sender=model)

    def connect_related_signals(self, related_model):
        from .signals import clear_related_instance  # NOQA - Prevent circular import

        signals.post_save.connect(clear_related_instance, sender=related_model)
        signals.pre_delete.connect(clear_related_instance, sender=related_model)

    def get(self, model):
        return self._registry.get(model, [])

    def get_related(self, model):
        return self._related_registry.get(model, "")

    def autodiscover(self):
        autodiscover_modules("serializers")


# This global object represents the default CacheRegistry, for the common case.
# You can instantiate CacheRegistry in your own code to create a custom
# register.
cache_registry = CacheRegistry()
