# from __future__ import annotations
import time
from typing import *
from store import Store


# TODO: Maybe s/Component/InventoryItem/g
class Component:

    # Base fields that all components have in common
    loadable_base_fields = ['key1', 'last_update']

    # Loadable fields are supposed to hold attributes that are
    # good to be persisted to and loaded from the store.
    # These should not contain dynamic data such as `daemon.running` or similar
    # data that could lead to issues if getting stale.
    loadable_fields = [] + loadable_base_fields

    def __init__(self, mgr=None, host=None, **kwargs):
        if not kwargs or not mgr or not host:
            return
        self.mgr = mgr
        self.host = host
        self.version = None
        self.last_update = None
        # When the components get loaded from the mon_store
        # we should trigger a refresh from the actual
        # source of data (bin/cephadm i.e.). The mgr might
        # have been down for a while and the data is now stale.
        self._needs_refresh: bool = True
        print(f"Loading kwargs -> {kwargs}")
        for k, v in kwargs.items():
            if k not in self.loadable_fields:
                print(f"field <{k}> is not supported in class <{self.__class__.__name__}>")
                continue
            self.__setattr__(k, v, notify=False)
        self.store = self.init_store()
        print(f"Loading component {self} on host {host}")

    def init_store(self):
        """
        Load the dynamically namespaced `Store`
        """
        assert self.host is not None
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
            if notify and hasattr(self, 'store'):
                self.notify_on_change()
        super(Component, self).__setattr__(key, value)

    def notify_on_change(self):
        print("A loadable_field was changed. This triggers a save() operation")
        self.save()

    def save(self):
        # Q: We potentially queue up a lot of save() operations when attributes are changed
        #    in rapid succession. Maybe only save if a threshold | time_past is reached.
        self.store.save(data=self.to_json())

    @property
    def needs_refresh(self):
        """
        Signalizes if the components needs a refresh (calling source()).
        There are some factors that influence this.

        * Time period has passed.
          Daemons for example will be periodically checked.
        * Adding new hosts
        """
        if self._needs_refresh:
            print(f"{self} needs refresh. _needs_refresh is True")
            return True
        if not self.last_update:
            print(f"{self} needs refresh. last_update is not set")
            return True
        if self.last_update:
            print(f"{self} needs refresh. Stale time has passed")
            if time.time() - self.last_update > 5:
                return True
        return False

    @classmethod
    def source(cls, mgr, host, data=None):
        """
        A custom method that describes how to source data (other than from the store)
        """
        print(f"source() is not implemented for {cls}")
        obj = cls(mgr=mgr, host=host)
        obj._needs_refresh = False
        obj.last_update = time.time()
        return obj

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.to_json() == other.to_json())

    def __hash__(self):
        return hash(self.to_json())

    def __repr__(self):
        printable_fields = {k: v for (k, v) in self.__dict__.items() if k in self.loadable_fields}
        return f"{self.__class__.__name__}({printable_fields})"


class DaemonDescription(Component):

    loadable_fields = ['daemon_id', 'daemon_type', 'etc'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(DaemonDescription, self).__init__(**kwargs)

    @classmethod
    def source(cls, mgr, host, data: Dict[str, str] = None) -> 'DaemonDescription':
        """
        This is a dummy method to parse data from bin/cephadm and compose an DaemonDescription object.
        """
        dd = cls(mgr=mgr, host=host)
        dd.last_update = time.time()
        cls.daemon_id = data.get('daemon_id')
        cls.daemon_type = data.get('daemon_type')
        cls.container_image = data.get('container_image')
        cls.last_refresh = time.time()
        cls._needs_refresh = False
        print(f"Sourced a {dd.component_name} -> from external data {dd}")
        return dd


class Network(Component):

    loadable_fields = ['address', 'subnet'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Network, self).__init__(**kwargs)


class Attribute(Component):

    loadable_fields = ['cpu', 'ram', 'os'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Attribute, self).__init__(**kwargs)


class Device(Component):

    loadable_fields = ['path', 'rotational', 'model'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Device, self).__init__(**kwargs)


class Config(Component):

    loadable_fields = ['foo', 'bar', 'baz'] + Component.loadable_base_fields

    def __init__(self, **kwargs):
        super(Config, self).__init__(**kwargs)


class ComponentCollection:
    """
    To have a common interface with `Component`. Now we can use

     * to_json()
     * from_json
     * foo.bar = 'baz'
     * baz = foo.bar
     * [x for x in foo]
     * x[0]

     Just like with a non-list(flat) type Component.
    """

    base_component = None

    def __init__(self, components: Optional[List[Component]] = None):
        # self.__components is 'private' (pseudo private)
        self.__components = components
        if not self.__components:
            self.__components = []

    def to_json(self) -> List[Dict[str, str]]:
        return [c.to_json() for c in self.__components]

    @classmethod
    def from_json(cls, data, mgr, host):
        cls.__components = [cls.base_component.from_json(c, mgr, host) for c in data]
        return cls()

    def save(self):
        """
        Forcefully save, this should however be handled via __setattr__ and notify()
        """
        return [c.save() for c in self.__components]

    def __setattr__(self, key, value):
        return [c.__setattr__(key, value) for c in self.__components]

    def __getattr__(self, item):
        return [c.__getattribute__(item) for c in self.__components]

    @classmethod
    def source(cls, mgr, hostname: str, data=None):
        data: List[Dict[str, str]] = mgr.run_cephadm(f'cephadm run ceph-volume inventory on host {hostname}')
        # This yields multiple entries for the hosts daemons detected by cephadm
        components = list()
        for daemon_data in data:
            components.append(cls.base_component.source(mgr, hostname, daemon_data))
        return cls(components)

    @property
    def component_name(self):
        return self.__class__.__name__.lower()

    def needs_refresh(self):
        return any([c.needs_refresh for c in self.__components])

    def __iter__(self):
        for component in self.__components:
            yield component

    def __getitem__(self, item):
        return self.__components[item]


class Devices(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """

    base_component = Device

    def __init__(self, components=None):
        super(Devices, self).__init__(components)


class Networks(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """

    base_component = Network

    def __init__(self, components=None):
        super(Networks, self).__init__(components)


class Attributes(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """

    base_component = Attribute

    def __init__(self, components=None):
        super(Attributes, self).__init__(components)


class Configs(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """

    base_component = Config

    def __init__(self, components=None):
        super(Configs, self).__init__(components)


class DaemonDescriptions(ComponentCollection):
    """
    If a Component can have multiple entries, there needs to an interface to them
    """

    base_component = DaemonDescription

    @property
    def component_name(self):
        """ Irregular naming """
        return 'daemons'

    def __init__(self, components=None):
        super(DaemonDescriptions, self).__init__(components)

