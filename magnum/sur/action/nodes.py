'''
Created on Aug 9, 2015

'''

import json


class Node(object):
    base_url = '/nodes'
    
    @classmethod
    def node_list(cls, sc):
        return sc.get(cls.base_url)
    
    @classmethod
    def node_create(cls, sc, name, cluster_name, profile_name):
        args = {
            'node': {
                'name': name,
                'cluster_id': cluster_name,
                'profile_id': profile_name,
                'role': None,
                'metadata': {}
            }
        }
        return sc.post(cls.base_url, data=json.dumps(args))
    
    @classmethod
    def node_update(cls):
        pass
    
    @classmethod
    def node_delete(cls):
        pass
