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
        self.store = Store(mgr, 'inventory.', version=self.requested_version)
        # Instead of `List[Host]` add a `Hosts` to be uniform with Component(s)
        self.hosts = Hosts()
        self.load_from_store()

    def load_from_store(self):
        """
        Load from the mon_store.

        This should happen on object creation.

        This method contains custom logic for populating attributes.
        """
        for ident, data in self.store.load():
            self.ident = ident
            self.loaded_version = data.pop('version')
            for host, component in data.items():
                print(f"Loading components for host <{host}>")
                host = Host(hostname=host, mgr=self.mgr)
                host.populate_inventory(component)
                self.hosts.append(host)

        assert self.loaded_version == self.requested_version

