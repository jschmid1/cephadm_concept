import json
from typing import *


class Store:
    """
    TODO: Maybe implement a database like interface for the mgr_store..
          CRUD could be helpful here
    """

    def __init__(self, mgr, namespace, version=2):
        self.mgr = mgr
        self.namespace = namespace
        self.version = version

    def save(self, data=None) -> bool:
        """
        Save `blob` to store.

        Example call to this function would look like:

        `self.store.save("spec/host_a/config", {'foo': 'bar'})`

        raise Exception if an issue is encountered

        // There are trade-offs between having a flat vs. non-flat hierarchy.
        // I do however think that having a non-flat hierarchy will benefit
        // us in this scenario. This may reflect in the need for a lower amount
        // of auxiliary functions. (map host to daemon, sort by type etc)
        // as everything is in one place.

        // This approach is overcoming the drawbacks of the non-flat hierarchy approach
        // by giving each component their own namespace which allows us to update them
        // individually without having to re-write the entire inventory/host blob.
        """
        assert data
        print(f"Saving in namespace -> {self.namespace}")
        print(f"Saving data -> {data}")
        # TODO: bug, existing store data is not being loaded
        old = self.mgr.get_store_prefix(self.namespace, version=self.version)
        if self.has_changes(data, old):
            print("Changes detected. Writing to store")
            return self.mgr.set_store(self.namespace, self.jsonify(data), version=self.version)
        print("No changes. Not writing to the store")
        return True

    @staticmethod
    def jsonify(data) -> Optional[str]:
        try:
            return json.dumps(data)
        except json.JSONDecodeError:
            # TODO: catch correct json errors
            raise Exception("Error encoding json")

    @staticmethod
    def has_changes(new=None, old=None) -> bool:
        """
        If we only write whole data blobs we can easily compute if we need to write
        to the store. Computing the *actual* diff is a bit more complicated.
        """
        print("Comparing existing data with new.")
        print(f"old -> {old}")
        print(f"new -> {new}")
        return new != old

    def load(self) -> Generator[str, Dict[Any, Any], Any]:
        """
        Load from the mon_store.

        This should only happen on object creation (ceph-mgr startup).
        """
        for k, v in self.mgr.get_store_prefix(self.namespace, version=self.version).items():
            yield k, v

    def migrate(self, from_v, to_v):
        # TODO!
        assert from_v > to_v

