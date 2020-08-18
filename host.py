from typing import *
from store import Store
from components import Networks, Devices, Attributes, DaemonDescriptions, Configs

STORABLE_COMPONENTS_MAP = {'networks': Networks,
                           'attributes': Attributes,
                           'configs': Configs,
                           'devices': Devices,
                           'daemons': DaemonDescriptions}


class Host:
    """
    The Host class has instances of `storable_components` loaded dynamically.
    This makes it easy to retrieve information about the host and its inventory.
    """

    storable_components = list(STORABLE_COMPONENTS_MAP.keys())

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
        self.attributes: Optional[Attributes] = None
        self.configs: Optional[Configs] = None
        self.devices: Optional[Devices] = None
        self.daemons: Optional[DaemonDescriptions] = None
        # end static init

    def online_daemons(self):
        return [x for x in self.daemons if x.running is True]

    def avail_devices(self):
        return [x for x in self.devices if x.available is True]

    def offline_daemons(self):
        return [x for x in self.daemons if x.running is not True]

    def namespace(self):
        return f"inventory/{self.hostname}"

    @property
    def inventory_objects(self):
        return filter(None, [self.__getattribute__(component)
                             for component in self.storable_components])

    @property
    def inventory_blueprints(self):
        return [STORABLE_COMPONENTS_MAP.get(component)
                for component in self.storable_components]

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
            if component_name == 'config':
                print('')
            component_instance = STORABLE_COMPONENTS_MAP.get(component_name)
            component_obj = component_instance.from_json(component_data, self.mgr, self.hostname)
            self.__setattr__(component_name, component_obj)

    def refresh_component(self):
        """
        Re-sourcing(refreshing) the data happens on the `host` level as all attributes are tied
        to the host.

        This method will check if a refresh is required and initiate it.

        A refresh can be initiated for:

        * Devices:
          Event from i.e. udev is detected, we should re-trigger a device refresh.
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
        return f"<Host({self.hostname})> ({printable_fields})"


class Hosts:

    def __init__(self, hosts: List[Host] = None):
        self.__hosts = hosts
        if not hosts:
            self.__hosts = []

    def __iter__(self):
        for host in self.__hosts:
            yield host

    def __getitem__(self, item):
        return self.__hosts[item]

    def append(self, host: Host):
        for component in host.inventory_blueprints:
            # If a host is getting added and there is no existing
            # data in the mon_store, source it!
            component_obj = component.source(host.mgr, host.hostname)
            host.__setattr__(component_obj.component_name, component_obj)
        self.__hosts.append(host)

    def remove(self, host):
        # TODO: Also remove it from the mon_store.
        #       removing the object should call self.store.del
        #       use __del__
        self.__hosts.remove(host)

    def __repr__(self):
        return f"<Hosts [{len(self.__hosts)}]>"
