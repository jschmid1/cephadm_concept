import pprint

import yaml


def _load_inventory_struct():
    with open('inventory_schema.yaml', 'rb') as _fd:
        return yaml.safe_load(_fd)


pp = pprint.PrettyPrinter(indent=2)
store_struct = _load_inventory_struct()
pp.pprint(store_struct)


class Mgr:
    """
    This is the MgrModule that implements interaction with the mgr-daemon, the mon store
    and more. Interesting methods are:

    * osdmap
    * osd_df
    * monmap
    * osd metadata
    * config store handling
    * ... and more

    """
    def get_store_prefix(self, namespace=None, version=None):
        if version == 1:
            return {
                "cephadm-dev": {
                    "hostname": "cephadm-dev",
                    "addr": "cephadm-dev",
                    "labels": [],
                    "status": ""
                },
                "cephadm-dev-2": {
                    "hostname": "cephadm-dev-2",
                    "addr": "cephadm-dev-2",
                    "labels": [],
                    "status": ""
                }
            }
        if version == 2:
            return _load_inventory_struct()

    def set_store(self, namespace, data, version=None):
        """
        This is the raw dump of the data into the mon_store
        """
        assert data
        assert namespace
        pass

