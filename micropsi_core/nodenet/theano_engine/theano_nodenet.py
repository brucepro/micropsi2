# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
import json
import os
import copy
import warnings

import theano
from theano import tensor as T
import numpy as np
import scipy.sparse as sp
import scipy

from micropsi_core.nodenet.nodenet import Nodenet
from micropsi_core.nodenet.node import Nodetype

from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_nodespace import *


STANDARD_NODETYPES = {
    # "Nodespace": {
    #    "name": "Nodespace"
    # },
    "Register": {
        "name": "Register",
        "slottypes": ["gen"],
        "nodefunction_name": "register",
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_name": "sensor",
        "gatetypes": ["gen"]
    },
    "Actor": {
        "name": "Actor",
        "parameters": ["datatarget"],
        "nodefunction_name": "actor",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
}

NODENET_VERSION = 1

NUMBER_OF_NODES = 50000
NUMBER_OF_ELEMENTS = NUMBER_OF_NODES * NUMBER_OF_ELEMENTS_PER_NODE


class TheanoNodenet(Nodenet):
    """
        theano runtime engine implementation
    """

    allocated_nodes = None
    last_allocated_node = -1

    # todo: get rid of positions
    positions = []

    # map of data sources to numerical node IDs
    sensormap = {}

    # map of numerical node IDs to data sources
    inverted_sensor_map = {}

    # map of data targets to numerical node IDs
    actuatormap = {}

    # map of numerical node IDs to data targets
    inverted_actuator_map = {}


    # theano tensors for performing operations
    w = None            # matrix of weights
    a = None            # vector of activations

    g_factor = None     # vector of gate factors, controlled by directional activators
    g_threshold = None  # vector of thresholds (gate parameters)
    g_amplification = None  # vector of amplification factors
    g_min = None        # vector of lower bounds
    g_max = None        # vector of upper bounds

    g_function_selector = None # vector of gate function selectors

    theta = None        # vector of thetas (i.e. biases)

    sparse = False

    @property
    def engine(self):
        return "theano_engine"

    @property
    def current_step(self):
        return self.__step

    @property
    def data(self):
        data = super(TheanoNodenet, self).data
        data['links'] = self.construct_links_dict()
        data['nodes'] = self.construct_nodes_dict()
        # for uid in data['nodes']:
        #    data['nodes'][uid]['gate_parameters'] = self.get_node(uid).clone_non_default_gate_parameters()
        data['nodespaces'] = self.construct_nodespaces_dict("Root")
        data['version'] = self.__version
        data['modulators'] = self.construct_modulators_dict()
        return data

    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}):

        super(TheanoNodenet, self).__init__(name or os.path.basename(filename), worldadapter, world, owner, uid)

        self.__version = NODENET_VERSION  # used to check compatibility of the node net data
        self.__step = 0
        self.__modulators = {}
        self.__nodetypes = STANDARD_NODETYPES
        self.filename = filename

        # for now, fix sparse to True
        self.sparse = True

        # this conversion of dicts to living objects in the same variable name really isn't pretty.
        # dict_nodenet is also doing it, and it's evil and should be fixed.
        # self.__nodetypes = {}
        # for type, data in STANDARD_NODETYPES.items():
        #    self.__nodetypes[type] = Nodetype(nodenet=self, **data)

        self.allocated_nodes = np.zeros(NUMBER_OF_NODES, dtype=np.int32)

        self.positions = [(10, 10) for i in range(0, NUMBER_OF_NODES)]

        if self.sparse:
            self.w = theano.shared(sp.csr_matrix((NUMBER_OF_ELEMENTS, NUMBER_OF_ELEMENTS), dtype=scipy.float32), name="w")
        else:
            w_matrix = np.zeros((NUMBER_OF_ELEMENTS, NUMBER_OF_ELEMENTS), dtype=np.float32)
            self.w = theano.shared(value=w_matrix.astype(T.config.floatX), name="w", borrow=True)

        a_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.a = theano.shared(value=a_array.astype(T.config.floatX), name="a", borrow=True)

        theta_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.theta = theano.shared(value=theta_array.astype(T.config.floatX), name="theta", borrow=True)

        g_factor_array = np.ones(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.g_factor = theano.shared(value=g_factor_array.astype(T.config.floatX), name="g_factor", borrow=True)

        g_threshold_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.g_threshold = theano.shared(value=g_threshold_array.astype(T.config.floatX), name="g_threshold", borrow=True)

        g_amplification_array = np.ones(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.g_amplification = theano.shared(value=g_amplification_array.astype(T.config.floatX), name="g_amplification", borrow=True)

        g_min_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.g_min = theano.shared(value=g_min_array.astype(T.config.floatX), name="g_min", borrow=True)

        g_max_array = np.ones(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.g_max = theano.shared(value=g_max_array.astype(T.config.floatX), name="g_max", borrow=True)

        g_function_selector_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.int8)
        self.g_function_selector = theano.shared(value=g_function_selector_array, name="gatefunction", borrow=True)

        self.rootnodespace = TheanoNodespace(self)

        self.stepoperators = [TheanoPropagate(self), TheanoCalculate(self)]
        self.stepoperators.sort(key=lambda op: op.priority)

        self.load()

    def load(self, string=None):
        """Load the node net from a file"""
        # try to access file
        with self.netlock:

            initfrom = {}

            if string:
                self.logger.info("Loading nodenet %s from string", self.name)
                try:
                    initfrom.update(json.loads(string))
                except ValueError:
                    warnings.warn("Could not read nodenet data from string")
                    return False
            else:
                try:
                    self.logger.info("Loading nodenet %s from file %s", self.name, self.filename)
                    with open(self.filename) as file:
                        initfrom.update(json.load(file))
                except ValueError:
                    warnings.warn("Could not read nodenet data")
                    return False
                except IOError:
                    warnings.warn("Could not open nodenet file")

            if self.__version == NODENET_VERSION:
                self.initialize_nodenet(initfrom)
                return True
            else:
                raise NotImplementedError("Wrong version of nodenet data, cannot import.")

    def initialize_nodenet(self, initfrom):
        """Called after reading new nodenet state.

        Parses the nodenet state and set up the non-persistent data structures necessary for efficient
        computation of the node net
        """

        nodetypes = {}
        for type, data in self.__nodetypes.items():
            nodetypes[type] = Nodetype(nodenet=self, **data)
        self.__nodetypes = nodetypes

        # todo: implement native modules
        # native_modules = {}
        # for type, data in self.__native_modules.items():
        #     native_modules[type] = Nodetype(nodenet=self, **data)
        # self.__native_modules = native_modules
        #
        # self.__modulators = initfrom.get("modulators", {})

        # todo: implement nodespaces
        # set up nodespaces; make sure that parent nodespaces exist before children are initialized
        # self.__nodespaces = {}
        # self.__nodespaces["Root"] = TheanoNodespace(self) #, None, (0, 0), name="Root", uid="Root")

        # now merge in all init data (from the persisted file typically)
        self.merge_data(initfrom)

    def merge_data(self, nodenet_data):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""

        # Because of the horrible initialize_nodenet design that replaces existing dictionary objects with
        # Python objects between initial loading and first use, none of the nodenet setup code is reusable.
        # Instantiation should be a state-independent method or a set of state-independent methods that can be
        # called whenever new data needs to be merged in, initially or later on.
        # Potentially, initialize_nodenet can be replaced with merge_data.

        # net will have the name of the one to be merged into us
        self.name = nodenet_data['name']

        # todo: implement nodespaces
        # merge in spaces, make sure that parent nodespaces exist before children are initialized
        # nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        # for nodespace in nodespaces_to_merge:
        #    self.initialize_nodespace(nodespace, nodenet_data['nodespaces'])

        # merge in nodes
        for uid in nodenet_data.get('nodes', {}):
            data = nodenet_data['nodes'][uid]
            if data['type'] in self.__nodetypes or data['type'] in self.__native_modules:
                self.create_node(
                    data['type'],
                    data['parent_nodespace'],
                    data['position'],
                    name=data['name'],
                    uid=data['uid'],
                    parameters=data['parameters'],
                    gate_parameters=data['gate_parameters'])
                node = self.get_node(uid)
                for gatetype in data['gate_activations']:   # todo: implement sheaves
                    node.get_gate(gatetype).activation = data['gate_activations'][gatetype]['default']['activation']

                # self.__nodes[uid] = TheanoNode(self, **data)
                # pos = self.__nodes[uid].position
                # xpos = int(pos[0] - (pos[0] % 100))
                # ypos = int(pos[1] - (pos[1] % 100))
                # if xpos not in self.__nodes_by_coords:
                #     self.__nodes_by_coords[xpos] = {}
                #     if xpos > self.max_coords['x']:
                #         self.max_coords['x'] = xpos
                # if ypos not in self.__nodes_by_coords[xpos]:
                #     self.__nodes_by_coords[xpos][ypos] = []
                #     if ypos > self.max_coords['y']:
                #         self.max_coords['y'] = ypos
                # self.__nodes_by_coords[xpos][ypos].append(uid)
            else:
                warnings.warn("Invalid nodetype %s for node %s" % (data['type'], uid))

        # merge in links
        for uid in nodenet_data.get('links', {}):
            data = nodenet_data['links'][uid]
            self.create_link(
                data['source_node_uid'],
                data['source_gate_name'],
                data['target_node_uid'],
                data['target_slot_name'],
                data['weight']
            )

        # todo: implement monitors
        # for uid in nodenet_data.get('monitors', {}):
        #     data = nodenet_data['monitors'][uid]
        #     if 'classname' in data:
        #         if hasattr(monitor, data['classname']):
        #             getattr(monitor, data['classname'])(self, **data)
        #         else:
        #             self.logger.warn('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], uid))
        #     else:
        #         # Compatibility mode
        #         monitor.NodeMonitor(self, name=data['node_name'], **data)

    def step(self):
        # self.user_prompt = None                       # todo: re-introduce user prompts when looking into native modules
        if self.world is not None and self.world.agents is not None and self.uid in self.world.agents:
            self.world.agents[self.uid].snapshot()      # world adapter snapshot
                                                        # TODO: Not really sure why we don't just know our world adapter,
                                                        # but instead the world object itself

        with self.netlock:

            # self.timeout_locks()

            for operator in self.stepoperators:
                operator.execute(self, None, self.netapi)

            self.netapi._step()

            self.__step += 1

    def get_node(self, uid):
        if uid in self.get_node_uids():
            return TheanoNode(self, uid, self.allocated_nodes[from_id(uid)])
        else:
            return None

    def get_node_uids(self):
        return [to_id(id) for id in np.nonzero(self.allocated_nodes)[0]]

    def is_node(self, uid):
        return uid in self.get_node_uids()

    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_parameters=None):

        if uid is None:
            uid = -1
            while uid < 0:
                for i in range((self.last_allocated_node + 1), NUMBER_OF_NODES):
                    if self.allocated_nodes[i] == 0:
                        uid = i
                        break

            if uid < 0:
                for i in range(self.last_allocated_node - 1):
                    if self.allocated_nodes[i] == 0:
                        uid = i
                        break

            if uid < 0:
                self.logger.warning("Cannot find free id, all " + NUMBER_OF_NODES + " node entries already in use.")
                return None
        else:
            uid = from_id(uid)

        self.last_allocated_node = uid
        self.allocated_nodes[uid] = get_numerical_node_type(nodetype)
        self.positions[uid] = position

        if nodetype == "Sensor":
            datasource = parameters["datasource"]
            if datasource is not None:
                connectedsensors = self.sensormap.get(datasource, [])
                connectedsensors.append(uid)
                self.sensormap[datasource] = connectedsensors
                self.inverted_sensor_map[to_id(uid)] = datasource
        elif nodetype == "Actor":
            datatarget = parameters["datatarget"]
            if datatarget is not None:
                connectedactuators = self.actuatormap.get(datatarget, [])
                connectedactuators.append(uid)
                self.actuatormap[datatarget] = connectedactuators
                self.inverted_actuator_map[to_id(uid)] = datatarget

        node = self.get_node(to_id(uid))
        for gate, gate_parameters in gate_parameters.items():
            for gate_parameter in gate_parameters:
                node.set_gate_parameter(gate, gate_parameter, gate_parameters[gate_parameter])

        return to_id(uid)

    def delete_node(self, uid):

        # unlink
        self.get_node(uid).unlink_completely()

        # forget
        self.allocated_nodes[from_id(uid)] = 0

        # hint at the free ID
        self.last_allocated_node = from_id(uid) - 1

    def get_nodespace(self, uid):
        if uid == "Root":
            return self.rootnodespace
        else:
            return None

    def get_nodespace_uids(self):
        return ["Root"]

    def is_nodespace(self, uid):
        return uid == "Root"

    def create_nodespace(self, parent_uid, position, name="", uid=None, gatefunction_strings=None):
        pass

    def delete_nodespace(self, uid):
        pass

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)

        # todo: the interface for create_link makes no sense: it always returns true and a link object that is only
        # being used to query the UID which is useless
        links = self.get_node(source_node_uid).get_gate(gate_type).get_links()
        link = None
        for candidate in links:
            if candidate.target_slot.type == slot_type and candidate.target_node.uid == target_node_uid:
                link = candidate
                break

        return True, link

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        ngt = get_numerical_gate_type(gate_type)
        nst = get_numerical_gate_type(slot_type)
        w_matrix = self.w.get_value(borrow=True, return_internal_type=True)
        x = from_id(target_node_uid) * NUMBER_OF_ELEMENTS_PER_NODE + nst
        y = from_id(source_node_uid) * NUMBER_OF_ELEMENTS_PER_NODE + ngt
        if self.sparse:
            w_matrix[x, y] = weight
        else:
            w_matrix[x][y] = weight
        self.w.set_value(w_matrix, borrow=True)
        return True

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, 0)

    def reload_native_modules(self, native_modules):
        pass

    def get_nodespace_area_data(self, nodespace_uid, x1, x2, y1, y2):
        return self.data                    # todo: implement

    def get_nodespace_data(self, nodespace_uid, max_nodes):
        return self.data                    # todo: implement

    def is_locked(self, lock):
        pass

    def is_locked_by(self, lock, key):
        pass

    def lock(self, lock, key, timeout=100):
        pass

    def unlock(self, lock):
        pass

    def get_modulator(self, modulator):
        pass

    def change_modulator(self, modulator, diff):
        pass

    def set_modulator(self, modulator, value):
        pass

    def get_nodetype(self, type):
        if type in self.__nodetypes:
            return self.__nodetypes[type]
        else:
            return None
            # return self.__native_modules.get(type)         # todo: implement native modules

    def construct_links_dict(self):
        data = {}
        for node_uid in self.get_node_uids():
            links = self.get_node(node_uid).get_associated_links()
            for link in links:
                data[link.uid] = link.data
        return data

    def construct_nodes_dict(self, max_nodes=-1):
        data = {}
        i = 0
        for node_uid in self.get_node_uids():
            i += 1
            data[node_uid] = self.get_node(node_uid).data
            if max_nodes > 0 and i > max_nodes:
                break
        return data

    def construct_nodespaces_dict(self, nodespace_uid):
        data = {}
        for nodespace_candidate_uid in self.get_nodespace_uids():
            if self.get_nodespace(nodespace_candidate_uid).parent_nodespace == nodespace_uid or nodespace_candidate_uid == nodespace_uid:
                data[nodespace_candidate_uid] = self.get_nodespace(nodespace_candidate_uid).data
        return data

    def construct_modulators_dict(self):
        return {}

    def update_node_positions(self):
        pass

    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        return copy.deepcopy(STANDARD_NODETYPES)

    def set_sensors_and_actuator_feedback_to_values(self, datasource_to_value_map, datatarget_to_value_map):
        """
        Sets the sensors for the given data sources to the given values
        """

        a_array = self.a.get_value(borrow=True, return_internal_type=True)

        for datasource in datasource_to_value_map:
            value = datasource_to_value_map.get(datasource)
            sensor_uids = self.sensormap.get(datasource, [])

            for sensor_uid in sensor_uids:
                a_array[sensor_uid * NUMBER_OF_ELEMENTS_PER_NODE + GEN] = value

        for datatarget in datatarget_to_value_map:
            value = datatarget_to_value_map.get(datatarget)
            actuator_uids = self.actuatormap.get(datatarget, [])

            for actuator_uid in actuator_uids:
                a_array[actuator_uid * NUMBER_OF_ELEMENTS_PER_NODE + GEN] = value

        self.a.set_value(a_array, borrow=True)

    def read_actuators(self):
        """
        Returns a map of datatargets to values for writing back to the world adapter
        """

        actuator_values_to_write = {}

        a_array = self.a.get_value(borrow=True, return_internal_type=True)

        for datatarget in self.actuatormap:
            actuator_node_activations = 0
            for actuator_id in self.actuatormap[datatarget]:
                index = actuator_id * NUMBER_OF_ELEMENTS_PER_NODE + GEN
                actuator_node_activations += a_array[actuator_id * NUMBER_OF_ELEMENTS_PER_NODE + GEN]

            actuator_values_to_write[datatarget] = actuator_node_activations

        self.a.set_value(a_array, borrow=True)

        return actuator_values_to_write