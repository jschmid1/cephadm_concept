from typing import *
from store import Store
from components import Network, Networks, Device, Devices, Attribute, DaemonDescription, DaemonDescriptions, Config


class Host:
    """
    The Host class has instances of `storable_components` loaded dynamically.
    This makes it easy to retrieve information about the host and its inventory.
    """

    storable_components_map = {'networks': Networks,
                               'attributes': Attribute,
                               'config': Config,
                               'devices': Devices,
                               'daemons': DaemonDescriptions}

    storable_components = list(storable_components_map.keys())

    def __init__(self, hostname, mgr=None):
        self.mgr = mgr
        self.hostname = hostname
        self.needs_refresh = False
        self.requested_version = 2  # This can come from the module config
        # TODO: hostnames can change. Account for that.
        self.store = Store(mgr, self.namespace(), version=self.requested_version)

        # statically initialize `storable_components`. This is just needed
        # to resolve and type-check attributes during development
        self.networks: Optional[Networks] = None
        self.attributes: Optional[Attribute] = None
        self.config: Optional[Config] = None
        self.devices: Optional[Devices] = None
        self.daemons: Optional[DaemonDescriptions] = None
        # end static init

    def online_daemons(self):
        return [x for x in self.daemons if x.running is True]

    def namespace(self):
        return f"inventory/{self.hostname}"

    @property
    def inventory_objects(self):
        return [self.__getattribute__(component) for component in self.storable_components]

    def populate_inventory(self, component):
        for component_name, component_data in component.items():
            print(f"Loading component -> {component_name}")
            """
            There are different types of components which can be identified by their
            return type:

            List:

            These components consists of multiple entries (i.e. Devices, Daemons, Networks etc)

            Dict:

            Those are flat `key: value` pairs (i.e. Attribute, Config)
            """
            component_collection = self.storable_components_map.get(component_name)
            component_collection.from_json(component_data)

    def refresh_component(self):
        """
        Re-sourcing(refreshing) the data happens on the `host` level as all attributes are tied
        to the host.

        This method will check if a refresh is required and initiate it.

        A refresh can be initiated for:

        * Devices:
          Event from i.e. udev is detected, we should retrigger a device refresh.
        * Networks:
          Event from kernel, udev
        * Daemons:
          After daemon deployment, refresh the inventory
        * Host:
          A new host is added and the components are loaded
        """
        pass

    def __repr__(self):
        printable_fields = {k: v for (k, v) in self.__dict__.items() if k in self.storable_components}
        return f"{self.__class__.__name__}({printable_fields})"

