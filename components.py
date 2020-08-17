from typing import *
from store import Store


# TODO: Maybe s/Component/InventoryItem/g
class Component:

    # Base fields that all components have in common
    loadable_base_fields = ['key1']

    # Loadable fields are supposed to hold attributes that are
    # good to be persisted to and loaded from the store.
    # These should not contain dynamic data such as `daemon.running` or similar
    # data that could lead to issues if getting stale.
    loadable_fields = [] + loadable_base_fields

    def __init__(self, mgr=None, host=None, **kwargs):
        print(f"Loading kwargs -> {kwargs}")
        self.mgr = mgr
        self.host = host
        self.version = None
        self.needs_refresh: bool = False
        self.store = self.init_store()
        for k, v in kwargs.items():
            if k not in self.loadable_fields:
                print(f"field <{k}> is not supported in class <{self.__class__.__name__}>")
                continue
            self.__setattr__(k, v, notify=False)

    def init_store(self):
        """
        Load the dynamically namespaced `Store`
        """
        return Store(self.mgr,
                     self.namespace(self.host),
                     version=self.version)

    @property
    def component_name(self):
        return self.__class__.__name__.lower()

    def namespace(self, host):
        """
        Components have a dynamic namespace based on the hostname and the
        `component_name`.

        TODO: Find a rule for pluralization/singularization
              Currently we're overwriting methods if it's NOT pluralizable
        """
        return f"inventory/{host}/{self.component_name}s"

    @classmethod
    def from_json(cls, data, mgr, host) -> 'Component':
        print(f"Loading {cls} from json")
        return cls(mgr=mgr, host=host, **{
            key: data.get(key, None)
            for key in cls.loadable_fields
        })

    def to_json(self) -> dict:
        # to_json all fields that are in loadable_fields and are not None (reduces the clutter)
        return {field: value for (field, value) in self.__dict__.items()
                if all([field in self.loadable_fields, field is not None])}

    def __setattr__(self, key, value, notify=True):
        if (not hasattr(self, key) or getattr(self, key) != value) and key in self.loadable_fields:
            if notify:
                self.notify_on_change()
        super(Component, self).__setattr__(key, value)

    def notify_on_change(self):
        print("A loadable_field was changed. This triggers a save() operation")
        self.save()

    def save(self):
        # Q: We potentially queue up a lot of save() operations when attributes are changed
        #    in rapid succession. Maybe only save if a threshold | time_past is reached.
        self.store.save(data=self.to_json())

    def source(self):
        """
        A custom method that describes how to source data (other than from the store)
        """
        pass

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.to_json() == other.to_json)

    def __hash__(self):
        return hash(self.to_json())

    def __repr__(self):
        printable_fields = {k: v for (k, v) in self.__dict__.items() if k in self.loadable_fields}
        return f"{self.component_name}({printable_fields})"


class ComponentCollection:

    def __init__(self, components: Optional[List[Component]]):
        self.components = components
        if not self.components:
            self.components = []

    def to_json(self):
        return [c.to_json() for c in self.components]

    def from_json(self):
        return [c.from_json for c in self.components]

    def __setattr__(self, key, value):
        return [c.__setattr__(key, value) for c in self.components]

    def __getattr__(self, item):
        return [c.__getattribute__ for c in self.components]


class DaemonDescription(Component):

    loadable_fields = ['daemon_id', 'daemon_type', 'etc'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(DaemonDescription, self).__init__(**kwargs)


class DaemonDescriptions(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """
    def __init__(self, components):
        super(DaemonDescriptions, self).__init__(components)


class Network(Component):

    loadable_fields = ['address', 'subnet'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Network, self).__init__(**kwargs)


class Networks(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """
    def __init__(self, components):
        super(Networks, self).__init__(components)


class Attribute(Component):

    loadable_fields = ['cpu', 'ram', 'os'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Attribute, self).__init__(**kwargs)


class Device(Component):

    loadable_fields = ['path', 'rotational', 'model'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Device, self).__init__(**kwargs)


class Devices(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """
    def __init__(self, components):
        super(Devices, self).__init__(components)


class Config(Component):

    loadable_fields = ['foo', 'bar', 'baz'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Config, self).__init__(**kwargs)

    def namespace(self, host):
        """
        Exception: Singularize (overwrite)
        """
        return f"inventory/{host}/{self.component_name}"

