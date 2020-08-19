from store import Store
from host import Host, Hosts


class Inventory:
    """
    Contains a List of Hosts that are registered to the system
    """

    def __init__(self, mgr):
        self.mgr = mgr
        self.ident = None
        self.requested_version = 2  # This can come from the module config
        self.loaded_version = None
        self.store = Store(mgr, version=self.requested_version)
        # Instead of `List[Host]` add a `Hosts` to be uniform with Component(s)
        self.hosts = Hosts()
        self.load_from_store()
        self.load_from_source()

    def add_host(self, host: Host):
        self.hosts.append(host)

    def remove_host(self, host):
        self.hosts.remove(host)

    def load_from_store(self):
        """
        Load from the mon_store.

        This should happen on object creation.

        This method contains custom logic for populating attributes.
        """
        for ident, data in self.store.load('inventory.'):
            self.ident = ident
            self.loaded_version = data.pop('version')
            for host, component in data.items():
                print(f"Loading components for host <{host}>")
                host = Host(hostname=host, mgr=self.mgr)
                host.populate_inventory_from_store(component)
                self.hosts.append(host)

        assert self.loaded_version == self.requested_version

    def load_from_source(self):
        """
        If any host is in the Inventory we attempt to refresh the data
        of its components.

        Conditions:
        * if required (determined by component.needs_restart())
        """
        for host in self.hosts:
            host.refresh()

    def refresh(self):
        print(f"Triggering checks for refresh")
        self.load_from_source()

