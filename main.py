import json
import pprint
import time
import yaml
from typing import *

from inventory import Inventory
from mgr import Mgr


class Internal:
    """
    This represents the respective backend orchestrator implementation (for Rook, mgr/cephadm, ceph-ansible)

    This is running on the ceph-mgr and implements a busy-loop which is triggered by a configurable timer
    called `serve`.
    """
    def __init__(self):
        self.mgr = Mgr()
        self.inventory = Inventory(mgr=self.mgr)

    def serve(self):
        counter = 0
        while True:
            print("foo")
            counter += 1
            print(type(self.inventory.hosts[0].attributes))
            print(type(self.inventory.hosts[0].networks))
            self.inventory.hosts[0].devices[0].key1 = counter
            self.inventory.hosts[0].networks[0].key1 = counter
            self.inventory.hosts[0].attributes.key1 = counter
            self.inventory.hosts[0].refresh_component()

            time.sleep(3)
            pass

    def example_internal_method(self, blob: Any) -> Optional[Any]:
        """
        This is an example internal method that handles a *WRITE* request.

        It passes a `blob` of type Any and may return Any.
        (Keeping it vague here as it can return str, or any completion type object)

        To avoid long waiting times, hanging commands etc, the orchestrator backends
        return a `Future/Promise` basically saying that the task was accepted and will
        be executed when applicable.

        There are some things that are happening to reduce the feedback loop though:

        * Input validation
        ------------------
        // Technically this happens during object creation in the `example_external_method`
        // Putting it here to *conceptually* highlight the role of this method.
        // Other validation require data about the state of the cluster which isn't
        // available in the `example_external_method` space.

        This can detect missing fields, bad formatting, unsupported features etc.

        * System validation
        -------------------

        If you try to add something that would violate the principles of the cluster
        we can stop you right there.

        An example:

        // This is probably a bad example. Find a better one
        You're trying to add a gateway but there are no OSDs yet. The creation would
        fail as you can't save configuration (if stored in rados obj) or create pools.

        The mentioned validations should be quick and unnoticeable(speed wise) by the user.

        This method will eventually kick-off any according method that handles the respective
        case.
        """
        return self.example_handler_method(blob)

    def example_handler_method(self, blob):
        """
        After we successfully validated the input and ruled out any known
        complication we possibly, depending on the request, have to store something
        to the Store(). // Explained later
        For the sake of consistency we have to `raise` immediately if the `save` operation
        failed.
        """
        pass


class External:
    """
    This represents the orchestrator CLI.
    It is agnostic of any orchestrator specifics and calls
    methods implemented in a `Interface`.
    """

    def __init__(self):
        self.internal = Internal()

    def example_external_method(self, cmd="dummy command"):
        """
        This is an example user-facing method.

        There are two types of commands:

        * READ
        ------

        Commands like `ps`, `ls` etc.

        Those are not interesting for this purpose and will be omitted.

        * WRITE
        -------

        Here we're trying to change the state of the cluster by
        deploying daemons, changing configuration, adding hosts etc.
        The method is responsible for the following actions:

            - Parse json/yaml/args
            - Construct objects
            - Call the respective method

        In order to stay consistent we should operate in the following order:
        """
        print(f"Calling example method with cmd -> {cmd}")

        # TODO
        spec = object()
        dummy_data = dict(cmd='orch apply', spec=spec)

        return self.internal.example_internal_method(dummy_data)


if __name__ == '__main__':
    module = Internal()
    module.serve()
