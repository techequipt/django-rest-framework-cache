from .utils import clear_for_instance
from .registry import cache_registry


def clear_instance(sender, instance, **kwargs):
    """Calls cache cleaner for current instance"""
    clear_for_instance(instance)


def clear_related_instance(sender, instance, **kwargs):
    """Calls cache cleaner for instance based on relation in registy"""
    relations = cache_registry.get_related(sender)
    if cache_registry.get_related(sender):
        # Model has been registered as a relation
        objects = sender.objects.all().values_list(relations).distinct()
        for obj in objects:
            clear_instance(obj.__class__, obj)
