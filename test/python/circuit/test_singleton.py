# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=missing-function-docstring,missing-class-docstring


"""
Tests for singleton gate and instruction behavior
"""

import copy
import io
import pickle
import sys
import types
import unittest.mock
import uuid

from qiskit.circuit.library import (
    HGate,
    SXGate,
    CXGate,
    CZGate,
    CSwapGate,
    CHGate,
    CCXGate,
    XGate,
    C4XGate,
)
from qiskit.circuit import Measure, Reset
from qiskit.circuit import Clbit, QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.singleton import SingletonGate, SingletonInstruction
from qiskit.converters import dag_to_circuit, circuit_to_dag

from qiskit.test.base import QiskitTestCase


class TestSingletonGate(QiskitTestCase):
    """Qiskit SingletonGate tests."""

    def test_default_singleton(self):
        gate = HGate()
        new_gate = HGate()
        self.assertIs(gate, new_gate)

    def test_base_class(self):
        gate = HGate()
        self.assertIsInstance(gate, HGate)
        self.assertIs(gate.base_class, HGate)

    def test_label_not_singleton(self):
        gate = HGate()
        label_gate = HGate(label="special")
        self.assertIsNot(gate, label_gate)

    def test_condition_not_singleton(self):
        gate = HGate()
        condition_gate = HGate().c_if(Clbit(), 0)
        self.assertIsNot(gate, condition_gate)

    def test_raise_on_state_mutation(self):
        gate = HGate()
        with self.assertRaises(TypeError):
            gate.label = "foo"
        with self.assertRaises(TypeError):
            gate.condition = (Clbit(), 0)

    def test_labeled_condition(self):
        singleton_gate = HGate()
        clbit = Clbit()
        gate = HGate(label="conditionally special").c_if(clbit, 0)
        self.assertIsNot(singleton_gate, gate)
        self.assertEqual(gate.label, "conditionally special")
        self.assertEqual(gate.condition, (clbit, 0))

    def test_default_singleton_copy(self):
        gate = HGate()
        copied = gate.copy()
        self.assertIs(gate, copied)

    def test_label_copy(self):
        gate = HGate(label="special")
        copied = gate.copy()
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)

    def test_label_copy_new(self):
        gate = HGate()
        label_gate = HGate(label="special")
        self.assertIsNot(gate, label_gate)
        self.assertNotEqual(gate.label, label_gate.label)
        copied = gate.copy()
        copied_label = label_gate.copy()
        self.assertIs(gate, copied)
        self.assertIsNot(copied, label_gate)
        self.assertIsNot(copied_label, gate)
        self.assertIsNot(copied_label, label_gate)
        self.assertNotEqual(copied.label, label_gate.label)
        self.assertEqual(copied_label, label_gate)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

    def test_condition_copy(self):
        gate = HGate().c_if(Clbit(), 0)
        copied = gate.copy()
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)

    def test_condition_label_copy(self):
        clbit = Clbit()
        gate = HGate(label="conditionally special").c_if(clbit, 0)
        copied = gate.copy()
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)
        self.assertEqual(copied.label, "conditionally special")
        self.assertEqual(copied.condition, (clbit, 0))

    def test_deepcopy(self):
        gate = HGate()
        copied = copy.deepcopy(gate)
        self.assertIs(gate, copied)

    def test_deepcopy_with_label(self):
        gate = HGate(label="special")
        copied = copy.deepcopy(gate)
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)
        self.assertEqual(copied.label, "special")

    def test_deepcopy_with_condition(self):
        gate = HGate().c_if(Clbit(), 0)
        copied = copy.deepcopy(gate)
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)

    def test_condition_label_deepcopy(self):
        clbit = Clbit()
        gate = HGate(label="conditionally special").c_if(clbit, 0)
        copied = copy.deepcopy(gate)
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)
        self.assertEqual(copied.label, "conditionally special")
        self.assertEqual(copied.condition, (clbit, 0))

    def test_label_deepcopy_new(self):
        gate = HGate()
        label_gate = HGate(label="special")
        self.assertIsNot(gate, label_gate)
        self.assertNotEqual(gate.label, label_gate.label)
        copied = copy.deepcopy(gate)
        copied_label = copy.deepcopy(label_gate)
        self.assertIs(gate, copied)
        self.assertIsNot(copied, label_gate)
        self.assertIsNot(copied_label, gate)
        self.assertIsNot(copied_label, label_gate)
        self.assertNotEqual(copied.label, label_gate.label)
        self.assertEqual(copied_label, label_gate)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

    def test_control_a_singleton(self):
        singleton_gate = HGate()
        gate = HGate(label="special")
        ch = gate.control(label="my_ch")
        self.assertEqual(ch.base_gate.label, "special")
        self.assertIsNot(ch.base_gate, singleton_gate)

    def test_round_trip_dag_conversion(self):
        qc = QuantumCircuit(1)
        gate = HGate()
        qc.append(gate, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIs(qc.data[0].operation, out.data[0].operation)

    def test_round_trip_dag_conversion_with_label(self):
        gate = HGate(label="special")
        qc = QuantumCircuit(1)
        qc.append(gate, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(out.data[0].operation.label, "special")

    def test_round_trip_dag_conversion_with_condition(self):
        qc = QuantumCircuit(1, 1)
        gate = HGate().c_if(qc.cregs[0], 0)
        qc.append(gate, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(out.data[0].operation.condition, (qc.cregs[0], 0))

    def test_round_trip_dag_conversion_condition_label(self):
        qc = QuantumCircuit(1, 1)
        gate = HGate(label="conditionally special").c_if(qc.cregs[0], 0)
        qc.append(gate, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(out.data[0].operation.condition, (qc.cregs[0], 0))
        self.assertEqual(out.data[0].operation.label, "conditionally special")

    def test_condition_via_instructionset(self):
        gate = HGate()
        qr = QuantumRegister(2, "qr")
        cr = ClassicalRegister(1, "cr")
        circuit = QuantumCircuit(qr, cr)
        circuit.h(qr[0]).c_if(cr, 1)
        self.assertIsNot(gate, circuit.data[0].operation)
        self.assertEqual(circuit.data[0].operation.condition, (cr, 1))

    def test_is_mutable(self):
        gate = HGate()
        self.assertFalse(gate.mutable)
        label_gate = HGate(label="foo")
        self.assertTrue(label_gate.mutable)
        self.assertIsNot(gate, label_gate)

    def test_to_mutable(self):
        gate = HGate()
        self.assertFalse(gate.mutable)
        new_gate = gate.to_mutable()
        self.assertTrue(new_gate.mutable)
        self.assertIsNot(gate, new_gate)

    def test_to_mutable_setter(self):
        gate = HGate()
        self.assertFalse(gate.mutable)
        mutable_gate = gate.to_mutable()
        mutable_gate.label = "foo"
        mutable_gate.duration = 3
        mutable_gate.unit = "s"
        clbit = Clbit()
        mutable_gate.condition = (clbit, 0)
        self.assertTrue(mutable_gate.mutable)
        self.assertIsNot(gate, mutable_gate)
        self.assertEqual(mutable_gate.label, "foo")
        self.assertEqual(mutable_gate.duration, 3)
        self.assertEqual(mutable_gate.unit, "s")
        self.assertEqual(mutable_gate.condition, (clbit, 0))

    def test_to_mutable_of_mutable_instance(self):
        gate = HGate(label="foo")
        mutable_copy = gate.to_mutable()
        self.assertIsNot(gate, mutable_copy)
        self.assertEqual(mutable_copy.label, gate.label)
        mutable_copy.label = "not foo"
        self.assertNotEqual(mutable_copy.label, gate.label)

    def test_set_custom_attr(self):
        gate = SXGate()
        with self.assertRaises(TypeError):
            gate.custom_foo = 12345
        mutable_gate = gate.to_mutable()
        self.assertTrue(mutable_gate.mutable)
        mutable_gate.custom_foo = 12345
        self.assertEqual(12345, mutable_gate.custom_foo)

    def test_positional_label(self):
        gate = SXGate()
        label_gate = SXGate("I am a little label")
        self.assertIsNot(gate, label_gate)
        self.assertEqual(label_gate.label, "I am a little label")

    def test_immutable_pickle(self):
        gate = SXGate()
        self.assertFalse(gate.mutable)
        with io.BytesIO() as fd:
            pickle.dump(gate, fd)
            fd.seek(0)
            copied = pickle.load(fd)
        self.assertFalse(copied.mutable)
        self.assertIs(copied, gate)

    def test_mutable_pickle(self):
        gate = SXGate()
        clbit = Clbit()
        condition_gate = gate.c_if(clbit, 0)
        self.assertIsNot(gate, condition_gate)
        self.assertEqual(condition_gate.condition, (clbit, 0))
        self.assertTrue(condition_gate.mutable)
        with io.BytesIO() as fd:
            pickle.dump(condition_gate, fd)
            fd.seek(0)
            copied = pickle.load(fd)
        self.assertEqual(copied, condition_gate)
        self.assertTrue(copied.mutable)

    def test_uses_default_arguments(self):
        class MyGate(SingletonGate):
            def __init__(self, label="my label"):
                super().__init__("my_gate", 1, [], label=label)

        gate = MyGate()
        self.assertIs(gate, MyGate())
        self.assertFalse(gate.mutable)
        self.assertIs(gate.base_class, MyGate)
        self.assertEqual(gate.label, "my label")

        with self.assertRaisesRegex(TypeError, "immutable"):
            gate.label = None

    def test_suppress_singleton(self):
        # Mostly the test here is that the `class` statement passes; it would raise if it attempted
        # to create a singleton instance since there's no defaults.
        class MyAbstractGate(SingletonGate, create_default_singleton=False):
            def __init__(self, x):
                super().__init__("my_abstract", 1, [])
                self.x = x

        gate = MyAbstractGate(1)
        self.assertTrue(gate.mutable)
        self.assertEqual(gate.x, 1)
        self.assertIsNot(MyAbstractGate(1), MyAbstractGate(1))

    def test_singleton_with_default(self):
        # Explicitly setting the label to its default.
        gate = HGate(label=None)
        self.assertIs(gate, HGate())
        self.assertIsNot(gate, HGate(label="label"))

    def test_additional_singletons(self):
        additional_inputs = [
            ((1,), {}),
            ((2,), {"label": "x"}),
        ]

        class Discrete(SingletonGate, additional_singletons=additional_inputs):
            def __init__(self, n=0, label=None):
                super().__init__("discrete", 1, [], label=label)
                self.n = n

            @staticmethod
            def _singleton_lookup_key(n=0, label=None):  # pylint: disable=arguments-differ
                # This is an atypical usage - in Qiskit standard gates, the `label` being set
                # not-None should not generate a singleton, so should return a mutable instance.
                return (n, label)

        default = Discrete()
        self.assertIs(default, Discrete())
        self.assertIs(default, Discrete(0, label=None))
        self.assertEqual(default.n, 0)
        self.assertIsNot(default, Discrete(1))

        one = Discrete(1)
        self.assertIs(one, Discrete(1))
        self.assertIs(one, Discrete(1, label=None))
        self.assertEqual(one.n, 1)
        self.assertIs(one.label, None)

        two = Discrete(2, label="x")
        self.assertIs(two, Discrete(2, label="x"))
        self.assertIsNot(two, Discrete(2))
        self.assertEqual(two.n, 2)
        self.assertEqual(two.label, "x")

        # This doesn't match any of the defined singletons, and we're checking that it's not
        # spuriously cached without us asking for it.
        self.assertIsNot(Discrete(2), Discrete(2))

    def test_additional_singletons_copy(self):
        additional_inputs = [
            ((1,), {}),
            ((2,), {"label": "x"}),
        ]

        class Discrete(SingletonGate, additional_singletons=additional_inputs):
            def __init__(self, n=0, label=None):
                super().__init__("discrete", 1, [], label=label)
                self.n = n

            @staticmethod
            def _singleton_lookup_key(n=0, label=None):  # pylint: disable=arguments-differ
                return (n, label)

        default = Discrete()
        one = Discrete(1)
        two = Discrete(2, "x")
        mutable = Discrete(3)

        self.assertIsNot(default, default.to_mutable())
        self.assertEqual(default.n, default.to_mutable().n)
        self.assertIsNot(one, one.to_mutable())
        self.assertEqual(one.n, one.to_mutable().n)
        self.assertIsNot(two, two.to_mutable())
        self.assertEqual(two.n, two.to_mutable().n)
        self.assertIsNot(mutable, mutable.to_mutable())
        self.assertEqual(mutable.n, mutable.to_mutable().n)

        # The equality assertions in the middle are sanity checks that nothing got overwritten.

        self.assertIs(default, copy.copy(default))
        self.assertEqual(default.n, 0)
        self.assertIs(one, copy.copy(one))
        self.assertEqual(one.n, 1)
        self.assertIs(two, copy.copy(two))
        self.assertEqual(two.n, 2)
        self.assertIsNot(mutable, copy.copy(mutable))

        self.assertIs(default, copy.deepcopy(default))
        self.assertEqual(default.n, 0)
        self.assertIs(one, copy.deepcopy(one))
        self.assertEqual(one.n, 1)
        self.assertIs(two, copy.deepcopy(two))
        self.assertEqual(two.n, 2)
        self.assertIsNot(mutable, copy.deepcopy(mutable))

    def test_additional_singletons_pickle(self):
        additional_inputs = [
            ((1,), {}),
            ((2,), {"label": "x"}),
        ]

        class Discrete(SingletonGate, additional_singletons=additional_inputs):
            def __init__(self, n=0, label=None):
                super().__init__("discrete", 1, [], label=label)
                self.n = n

            @staticmethod
            def _singleton_lookup_key(n=0, label=None):  # pylint: disable=arguments-differ
                return (n, label)

        # Pickle needs the class to be importable.  We want the class to only be instantiated inside
        # the test, which means we need a little magic to make it pretend-importable.
        dummy_module = types.ModuleType("_QISKIT_DUMMY_" + str(uuid.uuid4()).replace("-", "_"))
        dummy_module.Discrete = Discrete
        Discrete.__module__ = dummy_module.__name__
        Discrete.__qualname__ = Discrete.__name__

        default = Discrete()
        one = Discrete(1)
        two = Discrete(2, "x")
        mutable = Discrete(3)

        with unittest.mock.patch.dict(sys.modules, {dummy_module.__name__: dummy_module}):
            # The singletons in `additional_singletons` are statics; their lifetimes should be tied
            # to the type object itself, so if we don't delete it, it should be eligible to be
            # reloaded from and produce the exact instances.
            self.assertIs(default, pickle.loads(pickle.dumps(default)))
            self.assertEqual(default.n, 0)
            self.assertIs(one, pickle.loads(pickle.dumps(one)))
            self.assertEqual(one.n, 1)
            self.assertIs(two, pickle.loads(pickle.dumps(two)))
            self.assertEqual(two.n, 2)
            self.assertIsNot(mutable, pickle.loads(pickle.dumps(mutable)))


class TestSingletonControlledGate(QiskitTestCase):
    """Qiskit SingletonGate tests."""

    def test_default_singleton(self):
        gate = CXGate()
        new_gate = CXGate()
        self.assertIs(gate, new_gate)

    def test_label_not_singleton(self):
        gate = CXGate()
        label_gate = CXGate(label="special")
        self.assertIsNot(gate, label_gate)

    def test_condition_not_singleton(self):
        gate = CZGate()
        condition_gate = CZGate().c_if(Clbit(), 0)
        self.assertIsNot(gate, condition_gate)

    def test_raise_on_state_mutation(self):
        gate = CSwapGate()
        with self.assertRaises(TypeError):
            gate.label = "foo"
        with self.assertRaises(TypeError):
            gate.condition = (Clbit(), 0)

    def test_labeled_condition(self):
        singleton_gate = CSwapGate()
        clbit = Clbit()
        gate = CSwapGate(label="conditionally special").c_if(clbit, 0)
        self.assertIsNot(singleton_gate, gate)
        self.assertEqual(gate.label, "conditionally special")
        self.assertEqual(gate.condition, (clbit, 0))

    def test_default_singleton_copy(self):
        gate = CXGate()
        copied = gate.copy()
        self.assertIs(gate, copied)

    def test_label_copy(self):
        gate = CZGate(label="special")
        copied = gate.copy()
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)

    def test_label_copy_new(self):
        gate = CZGate()
        label_gate = CZGate(label="special")
        self.assertIsNot(gate, label_gate)
        self.assertNotEqual(gate.label, label_gate.label)
        copied = gate.copy()
        copied_label = label_gate.copy()
        self.assertIs(gate, copied)
        self.assertIsNot(copied, label_gate)
        self.assertIsNot(copied_label, gate)
        self.assertIsNot(copied_label, label_gate)
        self.assertNotEqual(copied.label, label_gate.label)
        self.assertEqual(copied_label, label_gate)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

    def test_condition_copy(self):
        gate = CZGate().c_if(Clbit(), 0)
        copied = gate.copy()
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)

    def test_condition_label_copy(self):
        clbit = Clbit()
        gate = CZGate(label="conditionally special").c_if(clbit, 0)
        copied = gate.copy()
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)
        self.assertEqual(copied.label, "conditionally special")
        self.assertEqual(copied.condition, (clbit, 0))

    def test_deepcopy(self):
        gate = CXGate()
        copied = copy.deepcopy(gate)
        self.assertIs(gate, copied)

    def test_deepcopy_with_label(self):
        singleton_gate = CXGate()
        gate = CXGate(label="special")
        copied = copy.deepcopy(gate)
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)
        self.assertEqual(copied.label, "special")
        self.assertTrue(copied.mutable)
        self.assertIsNot(copied, singleton_gate)
        self.assertEqual(singleton_gate, copied)
        self.assertNotEqual(singleton_gate.label, copied.label)

    def test_deepcopy_with_condition(self):
        gate = CCXGate().c_if(Clbit(), 0)
        copied = copy.deepcopy(gate)
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)

    def test_condition_label_deepcopy(self):
        clbit = Clbit()
        gate = CHGate(label="conditionally special").c_if(clbit, 0)
        copied = copy.deepcopy(gate)
        self.assertIsNot(gate, copied)
        self.assertEqual(gate, copied)
        self.assertEqual(copied.label, "conditionally special")
        self.assertEqual(copied.condition, (clbit, 0))

    def test_label_deepcopy_new(self):
        gate = CHGate()
        label_gate = CHGate(label="special")
        self.assertIsNot(gate, label_gate)
        self.assertNotEqual(gate.label, label_gate.label)
        copied = copy.deepcopy(gate)
        copied_label = copy.deepcopy(label_gate)
        self.assertIs(gate, copied)
        self.assertIsNot(copied, label_gate)
        self.assertIsNot(copied_label, gate)
        self.assertIsNot(copied_label, label_gate)
        self.assertNotEqual(copied.label, label_gate.label)
        self.assertEqual(copied_label, label_gate)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

    def test_control_a_singleton(self):
        singleton_gate = CHGate()
        gate = CHGate(label="special")
        ch = gate.control(label="my_ch")
        self.assertEqual(ch.base_gate.label, "special")
        self.assertIsNot(ch.base_gate, singleton_gate)

    def test_round_trip_dag_conversion(self):
        qc = QuantumCircuit(2)
        gate = CHGate()
        qc.append(gate, [0, 1])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIs(qc.data[0].operation, out.data[0].operation)

    def test_round_trip_dag_conversion_with_label(self):
        gate = CHGate(label="special")
        qc = QuantumCircuit(2)
        qc.append(gate, [0, 1])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(out.data[0].operation.label, "special")

    def test_round_trip_dag_conversion_with_condition(self):
        qc = QuantumCircuit(2, 1)
        gate = CHGate().c_if(qc.cregs[0], 0)
        qc.append(gate, [0, 1])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(out.data[0].operation.condition, (qc.cregs[0], 0))

    def test_round_trip_dag_conversion_condition_label(self):
        qc = QuantumCircuit(2, 1)
        gate = CHGate(label="conditionally special").c_if(qc.cregs[0], 0)
        qc.append(gate, [0, 1])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(out.data[0].operation.condition, (qc.cregs[0], 0))
        self.assertEqual(out.data[0].operation.label, "conditionally special")

    def test_condition_via_instructionset(self):
        gate = CHGate()
        qr = QuantumRegister(2, "qr")
        cr = ClassicalRegister(1, "cr")
        circuit = QuantumCircuit(qr, cr)
        circuit.h(qr[0]).c_if(cr, 1)
        self.assertIsNot(gate, circuit.data[0].operation)
        self.assertEqual(circuit.data[0].operation.condition, (cr, 1))

    def test_is_mutable(self):
        gate = CXGate()
        self.assertFalse(gate.mutable)
        label_gate = CXGate(label="foo")
        self.assertTrue(label_gate.mutable)
        self.assertIsNot(gate, label_gate)

    def test_to_mutable(self):
        gate = CXGate()
        self.assertFalse(gate.mutable)
        new_gate = gate.to_mutable()
        self.assertTrue(new_gate.mutable)
        self.assertIsNot(gate, new_gate)

    def test_to_mutable_setter(self):
        gate = CZGate()
        self.assertFalse(gate.mutable)
        mutable_gate = gate.to_mutable()
        mutable_gate.label = "foo"
        mutable_gate.duration = 3
        mutable_gate.unit = "s"
        clbit = Clbit()
        mutable_gate.condition = (clbit, 0)
        self.assertTrue(mutable_gate.mutable)
        self.assertIsNot(gate, mutable_gate)
        self.assertEqual(mutable_gate.label, "foo")
        self.assertEqual(mutable_gate.duration, 3)
        self.assertEqual(mutable_gate.unit, "s")
        self.assertEqual(mutable_gate.condition, (clbit, 0))

    def test_to_mutable_of_mutable_instance(self):
        gate = CZGate(label="foo")
        mutable_copy = gate.to_mutable()
        self.assertIsNot(gate, mutable_copy)
        self.assertEqual(mutable_copy.label, gate.label)
        mutable_copy.label = "not foo"
        self.assertNotEqual(mutable_copy.label, gate.label)

    def test_inner_gate_label(self):
        inner_gate = HGate(label="my h gate")
        controlled_gate = inner_gate.control()
        self.assertTrue(controlled_gate.mutable)
        self.assertEqual("my h gate", controlled_gate.base_gate.label)

    def test_inner_gate_label_outer_label_too(self):
        inner_gate = HGate(label="my h gate")
        controlled_gate = inner_gate.control(label="foo")
        self.assertTrue(controlled_gate.mutable)
        self.assertEqual("my h gate", controlled_gate.base_gate.label)
        self.assertEqual("foo", controlled_gate.label)

    def test_inner_outer_label_with_c_if(self):
        inner_gate = HGate(label="my h gate")
        controlled_gate = inner_gate.control(label="foo")
        clbit = Clbit()
        conditonal_controlled_gate = controlled_gate.c_if(clbit, 0)
        self.assertTrue(conditonal_controlled_gate.mutable)
        self.assertEqual("my h gate", conditonal_controlled_gate.base_gate.label)
        self.assertEqual("foo", conditonal_controlled_gate.label)
        self.assertEqual((clbit, 0), conditonal_controlled_gate.condition)

    def test_inner_outer_label_with_c_if_deepcopy(self):
        inner_gate = XGate(label="my h gate")
        controlled_gate = inner_gate.control(label="foo")
        clbit = Clbit()
        conditonal_controlled_gate = controlled_gate.c_if(clbit, 0)
        self.assertTrue(conditonal_controlled_gate.mutable)
        self.assertEqual("my h gate", conditonal_controlled_gate.base_gate.label)
        self.assertEqual("foo", conditonal_controlled_gate.label)
        self.assertEqual((clbit, 0), conditonal_controlled_gate.condition)
        copied = copy.deepcopy(conditonal_controlled_gate)
        self.assertIsNot(conditonal_controlled_gate, copied)
        self.assertTrue(copied.mutable)
        self.assertEqual("my h gate", copied.base_gate.label)
        self.assertEqual("foo", copied.label)
        self.assertEqual((clbit, 0), copied.condition)

    def test_inner_outer_label_pickle(self):
        inner_gate = XGate(label="my h gate")
        controlled_gate = inner_gate.control(label="foo")
        self.assertTrue(controlled_gate.mutable)
        self.assertEqual("my h gate", controlled_gate.base_gate.label)
        self.assertEqual("foo", controlled_gate.label)
        with io.BytesIO() as fd:
            pickle.dump(controlled_gate, fd)
            fd.seek(0)
            copied = pickle.load(fd)
        self.assertIsNot(controlled_gate, copied)
        self.assertTrue(copied.mutable)
        self.assertEqual("my h gate", copied.base_gate.label)
        self.assertEqual("foo", copied.label)

    def test_singleton_with_defaults(self):
        self.assertIs(CXGate(), CXGate(label=None))
        self.assertIs(CXGate(), CXGate(duration=None, unit="dt"))
        self.assertIs(CXGate(), CXGate(_base_label=None))
        self.assertIs(CXGate(), CXGate(label=None, ctrl_state=None))

    def test_singleton_with_equivalent_ctrl_state(self):
        self.assertIs(CXGate(), CXGate(ctrl_state=None))
        self.assertIs(CXGate(), CXGate(ctrl_state=1))
        self.assertIs(CXGate(), CXGate(label=None, ctrl_state=1))
        self.assertIs(CXGate(), CXGate(ctrl_state="1"))
        self.assertIsNot(CXGate(), CXGate(ctrl_state=0))
        self.assertIsNot(CXGate(), CXGate(ctrl_state="0"))

        self.assertIs(C4XGate(), C4XGate(ctrl_state=None))
        self.assertIs(C4XGate(), C4XGate(ctrl_state=15))
        self.assertIs(C4XGate(), C4XGate(ctrl_state="1111"))
        self.assertIsNot(C4XGate(), C4XGate(ctrl_state=0))


class TestSingletonInstruction(QiskitTestCase):
    """Qiskit SingletonInstruction tests."""

    def test_default_singleton(self):
        measure = Measure()
        new_measure = Measure()
        self.assertIs(measure, new_measure)

        reset = Reset()
        new_reset = Reset()
        self.assertIs(reset, new_reset)

    def test_base_class(self):
        measure = Measure()
        self.assertIsInstance(measure, Measure)
        self.assertIs(measure.base_class, Measure)

        reset = Reset()
        self.assertIsInstance(reset, Reset)
        self.assertIs(reset.base_class, Reset)

    def test_label_not_singleton(self):
        measure = Measure()
        label_measure = Measure(label="special")
        self.assertIsNot(measure, label_measure)

        reset = Reset()
        label_reset = Reset(label="special")
        self.assertIsNot(reset, label_reset)

    def test_condition_not_singleton(self):
        measure = Measure()
        condition_measure = Measure().c_if(Clbit(), 0)
        self.assertIsNot(measure, condition_measure)

        reset = Reset()
        condition_reset = Reset().c_if(Clbit(), 0)
        self.assertIsNot(reset, condition_reset)

    def test_raise_on_state_mutation(self):
        measure = Measure()
        with self.assertRaises(TypeError):
            measure.label = "foo"
        with self.assertRaises(TypeError):
            measure.condition = (Clbit(), 0)

        reset = Reset()
        with self.assertRaises(TypeError):
            reset.label = "foo"
        with self.assertRaises(TypeError):
            reset.condition = (Clbit(), 0)

    def test_labeled_condition(self):
        singleton_measure = Measure()
        clbit = Clbit()
        measure = Measure(label="conditionally special").c_if(clbit, 0)
        self.assertIsNot(singleton_measure, measure)
        self.assertEqual(measure.label, "conditionally special")
        self.assertEqual(measure.condition, (clbit, 0))

        singleton_reset = Reset()
        clbit = Clbit()
        reset = Reset(label="conditionally special").c_if(clbit, 0)
        self.assertIsNot(singleton_reset, reset)
        self.assertEqual(reset.label, "conditionally special")
        self.assertEqual(reset.condition, (clbit, 0))

    def test_default_singleton_copy(self):
        measure = Measure()
        copied = measure.copy()
        self.assertIs(measure, copied)

        reset = Reset()
        copied = reset.copy()
        self.assertIs(reset, copied)

    def test_label_copy(self):
        measure = Measure(label="special")
        copied = measure.copy()
        self.assertIsNot(measure, copied)
        self.assertEqual(measure, copied)

        reset = Reset(label="special")
        copied = reset.copy()
        self.assertIsNot(reset, copied)
        self.assertEqual(reset, copied)

    def test_label_copy_new(self):
        measure = Measure()
        label_measure = Measure(label="special")
        self.assertIsNot(measure, label_measure)
        self.assertNotEqual(measure.label, label_measure.label)
        copied = measure.copy()
        copied_label = label_measure.copy()
        self.assertIs(measure, copied)
        self.assertIsNot(copied, label_measure)
        self.assertIsNot(copied_label, measure)
        self.assertIsNot(copied_label, label_measure)
        self.assertNotEqual(copied.label, label_measure.label)
        self.assertEqual(copied_label, label_measure)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

        reset = Reset()
        label_reset = Reset(label="special")
        self.assertIsNot(reset, label_reset)
        self.assertNotEqual(reset.label, label_reset.label)
        copied = reset.copy()
        copied_label = label_reset.copy()
        self.assertIs(reset, copied)
        self.assertIsNot(copied, label_reset)
        self.assertIsNot(copied_label, reset)
        self.assertIsNot(copied_label, label_reset)
        self.assertNotEqual(copied.label, label_reset.label)
        self.assertEqual(copied_label, label_reset)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

    def test_condition_copy(self):
        measure = Measure().c_if(Clbit(), 0)
        copied = measure.copy()
        self.assertIsNot(measure, copied)
        self.assertEqual(measure, copied)

        reset = Reset().c_if(Clbit(), 0)
        copied = reset.copy()
        self.assertIsNot(reset, copied)
        self.assertEqual(reset, copied)

    def test_condition_label_copy(self):
        clbit = Clbit()
        measure = Measure(label="conditionally special").c_if(clbit, 0)
        copied_measure = measure.copy()
        self.assertIsNot(measure, copied_measure)
        self.assertEqual(measure, copied_measure)
        self.assertEqual(copied_measure.label, "conditionally special")
        self.assertEqual(copied_measure.condition, (clbit, 0))

        clbit = Clbit()
        reset = Reset(label="conditionally special").c_if(clbit, 0)
        copied_reset = reset.copy()
        self.assertIsNot(reset, copied_reset)
        self.assertEqual(reset, copied_reset)
        self.assertEqual(copied_reset.label, "conditionally special")
        self.assertEqual(copied_reset.condition, (clbit, 0))

    def test_deepcopy(self):
        measure = Measure()
        copied = copy.deepcopy(measure)
        self.assertIs(measure, copied)

        reset = Reset()
        copied = copy.deepcopy(reset)
        self.assertIs(reset, copied)

    def test_deepcopy_with_label(self):
        measure = Measure(label="special")
        copied = copy.deepcopy(measure)
        self.assertIsNot(measure, copied)
        self.assertEqual(measure, copied)
        self.assertEqual(copied.label, "special")

        reset = Reset(label="special")
        copied = copy.deepcopy(reset)
        self.assertIsNot(reset, copied)
        self.assertEqual(reset, copied)
        self.assertEqual(copied.label, "special")

    def test_deepcopy_with_condition(self):
        measure = Measure().c_if(Clbit(), 0)
        copied = copy.deepcopy(measure)
        self.assertIsNot(measure, copied)
        self.assertEqual(measure, copied)

        reset = Reset().c_if(Clbit(), 0)
        copied = copy.deepcopy(reset)
        self.assertIsNot(reset, copied)
        self.assertEqual(reset, copied)

    def test_condition_label_deepcopy(self):
        clbit = Clbit()
        measure = Measure(label="conditionally special").c_if(clbit, 0)
        copied = copy.deepcopy(measure)
        self.assertIsNot(measure, copied)
        self.assertEqual(measure, copied)
        self.assertEqual(copied.label, "conditionally special")
        self.assertEqual(copied.condition, (clbit, 0))

        clbit = Clbit()
        reset = Reset(label="conditionally special").c_if(clbit, 0)
        copied = copy.deepcopy(reset)
        self.assertIsNot(reset, copied)
        self.assertEqual(reset, copied)
        self.assertEqual(copied.label, "conditionally special")
        self.assertEqual(copied.condition, (clbit, 0))

    def test_label_deepcopy_new(self):
        measure = Measure()
        label_measure = Measure(label="special")
        self.assertIsNot(measure, label_measure)
        self.assertNotEqual(measure.label, label_measure.label)
        copied = copy.deepcopy(measure)
        copied_label = copy.deepcopy(label_measure)
        self.assertIs(measure, copied)
        self.assertIsNot(copied, label_measure)
        self.assertIsNot(copied_label, measure)
        self.assertIsNot(copied_label, label_measure)
        self.assertNotEqual(copied.label, label_measure.label)
        self.assertEqual(copied_label, label_measure)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

        reset = Reset()
        label_reset = Reset(label="special")
        self.assertIsNot(reset, label_reset)
        self.assertNotEqual(reset.label, label_reset.label)
        copied = copy.deepcopy(reset)
        copied_label = copy.deepcopy(label_reset)
        self.assertIs(reset, copied)
        self.assertIsNot(copied, label_reset)
        self.assertIsNot(copied_label, reset)
        self.assertIsNot(copied_label, label_reset)
        self.assertNotEqual(copied.label, label_reset.label)
        self.assertEqual(copied_label, label_reset)
        self.assertNotEqual(copied.label, "special")
        self.assertEqual(copied_label.label, "special")

    def test_round_trip_dag_conversion(self):
        qc = QuantumCircuit(1, 1)
        measure = Measure()
        reset = Reset()
        qc.append(measure, [0], [0])
        qc.append(reset, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIs(qc.data[0].operation, out.data[0].operation)
        self.assertIs(qc.data[1].operation, out.data[1].operation)

    def test_round_trip_dag_conversion_with_label(self):
        measure = Measure(label="special_measurement")
        reset = Reset(label="special_reset")
        qc = QuantumCircuit(1, 1)
        qc.append(measure, [0], [0])
        qc.append(reset, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertIsNot(qc.data[1].operation, out.data[1].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[1].operation, out.data[1].operation)
        self.assertEqual(out.data[0].operation.label, "special_measurement")
        self.assertEqual(out.data[1].operation.label, "special_reset")

    def test_round_trip_dag_conversion_with_condition(self):
        qc = QuantumCircuit(1, 1)
        measure = Measure().c_if(qc.cregs[0], 0)
        reset = Reset().c_if(qc.cregs[0], 0)
        qc.append(measure, [0], [0])
        qc.append(reset, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertIsNot(qc.data[1].operation, out.data[1].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[1].operation, out.data[1].operation)
        self.assertEqual(out.data[0].operation.condition, (qc.cregs[0], 0))
        self.assertEqual(out.data[1].operation.condition, (qc.cregs[0], 0))

    def test_round_trip_dag_conversion_condition_label(self):
        qc = QuantumCircuit(1, 1)
        measure = Measure(label="conditionally special measurement").c_if(qc.cregs[0], 0)
        reset = Reset(label="conditionally special reset").c_if(qc.cregs[0], 0)
        qc.append(measure, [0], [0])
        qc.append(reset, [0])
        dag = circuit_to_dag(qc)
        out = dag_to_circuit(dag)
        self.assertIsNot(qc.data[0].operation, out.data[0].operation)
        self.assertIsNot(qc.data[1].operation, out.data[1].operation)
        self.assertEqual(qc.data[0].operation, out.data[0].operation)
        self.assertEqual(qc.data[1].operation, out.data[1].operation)
        self.assertEqual(out.data[0].operation.condition, (qc.cregs[0], 0))
        self.assertEqual(out.data[1].operation.condition, (qc.cregs[0], 0))
        self.assertEqual(out.data[0].operation.label, "conditionally special measurement")
        self.assertEqual(out.data[1].operation.label, "conditionally special reset")

    def test_condition_via_instructionset(self):
        measure = Measure()
        reset = Reset()
        qr = QuantumRegister(2, "qr")
        cr = ClassicalRegister(1, "cr")
        circuit = QuantumCircuit(qr, cr)
        circuit.measure(qr[0], cr[0]).c_if(cr, 1)
        circuit.reset(qr[0]).c_if(cr, 1)
        self.assertIsNot(measure, circuit.data[0].operation)
        self.assertIsNot(reset, circuit.data[1].operation)
        self.assertEqual(circuit.data[0].operation.condition, (cr, 1))
        self.assertEqual(circuit.data[1].operation.condition, (cr, 1))

    def test_is_mutable(self):
        measure = Measure()
        self.assertFalse(measure.mutable)
        label_measure = Measure(label="foo")
        self.assertTrue(label_measure.mutable)
        self.assertIsNot(measure, label_measure)

        reset = Reset()
        self.assertFalse(reset.mutable)
        label_reset = Reset(label="foo")
        self.assertTrue(label_reset.mutable)
        self.assertIsNot(reset, label_reset)

    def test_to_mutable(self):
        measure = Measure()
        self.assertFalse(measure.mutable)
        new_measure = measure.to_mutable()
        self.assertTrue(new_measure.mutable)
        self.assertIsNot(measure, new_measure)

        reset = Reset()
        self.assertFalse(reset.mutable)
        new_reset = reset.to_mutable()
        self.assertTrue(new_reset.mutable)
        self.assertIsNot(reset, new_reset)

    def test_to_mutable_setter(self):
        measure = Measure()
        self.assertFalse(measure.mutable)
        mutable_measure = measure.to_mutable()
        mutable_measure.label = "foo"
        mutable_measure.duration = 3
        mutable_measure.unit = "s"
        clbit = Clbit()
        mutable_measure.condition = (clbit, 0)
        self.assertTrue(mutable_measure.mutable)
        self.assertIsNot(measure, mutable_measure)
        self.assertEqual(mutable_measure.label, "foo")
        self.assertEqual(mutable_measure.duration, 3)
        self.assertEqual(mutable_measure.unit, "s")
        self.assertEqual(mutable_measure.condition, (clbit, 0))

        reset = Reset()
        self.assertFalse(reset.mutable)
        mutable_reset = reset.to_mutable()
        mutable_reset.label = "foo"
        mutable_reset.duration = 3
        mutable_reset.unit = "s"
        clbit = Clbit()
        mutable_reset.condition = (clbit, 0)
        self.assertTrue(mutable_reset.mutable)
        self.assertIsNot(reset, mutable_measure)
        self.assertEqual(mutable_reset.label, "foo")
        self.assertEqual(mutable_reset.duration, 3)
        self.assertEqual(mutable_reset.unit, "s")
        self.assertEqual(mutable_reset.condition, (clbit, 0))

    def test_to_mutable_of_mutable_instance(self):
        measure = Measure(label="foo")
        mutable_measure_copy = measure.to_mutable()
        self.assertIsNot(measure, mutable_measure_copy)
        self.assertEqual(mutable_measure_copy.label, measure.label)
        mutable_measure_copy.label = "not foo"
        self.assertNotEqual(mutable_measure_copy.label, measure.label)

        reset = Reset(label="foo")
        mutable_reset_copy = reset.to_mutable()
        self.assertIsNot(reset, mutable_reset_copy)
        self.assertEqual(mutable_reset_copy.label, reset.label)
        mutable_reset_copy.label = "not foo"
        self.assertNotEqual(mutable_reset_copy.label, reset.label)

    def test_set_custom_attr(self):
        measure = Measure()
        with self.assertRaises(TypeError):
            measure.custom_foo = 12345
        mutable_measure = measure.to_mutable()
        self.assertTrue(mutable_measure.mutable)
        mutable_measure.custom_foo = 12345
        self.assertEqual(12345, mutable_measure.custom_foo)

        reset = Reset()
        with self.assertRaises(TypeError):
            reset.custom_foo = 12345
        mutable_reset = reset.to_mutable()
        self.assertTrue(mutable_reset.mutable)
        mutable_reset.custom_foo = 12345
        self.assertEqual(12345, mutable_reset.custom_foo)

    def test_positional_label(self):
        measure = Measure()
        label_measure = Measure("I am a little label")
        self.assertIsNot(measure, label_measure)
        self.assertEqual(label_measure.label, "I am a little label")

        reset = Reset()
        label_reset = Reset("I am a big label")
        self.assertIsNot(reset, label_reset)
        self.assertEqual(label_reset.label, "I am a big label")

    def test_immutable_pickle(self):
        measure = Measure()
        self.assertFalse(measure.mutable)
        with io.BytesIO() as fd:
            pickle.dump(measure, fd)
            fd.seek(0)
            copied_measure = pickle.load(fd)
        self.assertFalse(copied_measure.mutable)
        self.assertIs(copied_measure, measure)

        reset = Reset()
        self.assertFalse(reset.mutable)
        with io.BytesIO() as fd:
            pickle.dump(reset, fd)
            fd.seek(0)
            copied_reset = pickle.load(fd)
        self.assertFalse(copied_reset.mutable)
        self.assertIs(copied_reset, reset)

    def test_mutable_pickle(self):
        measure = Measure()
        clbit = Clbit()
        condition_measure = measure.c_if(clbit, 0)
        self.assertIsNot(measure, condition_measure)
        self.assertEqual(condition_measure.condition, (clbit, 0))
        self.assertTrue(condition_measure.mutable)
        with io.BytesIO() as fd:
            pickle.dump(condition_measure, fd)
            fd.seek(0)
            copied_measure = pickle.load(fd)
        self.assertEqual(copied_measure, condition_measure)
        self.assertTrue(copied_measure.mutable)

        reset = Reset()
        clbit = Clbit()
        condition_reset = reset.c_if(clbit, 0)
        self.assertIsNot(reset, condition_reset)
        self.assertEqual(condition_reset.condition, (clbit, 0))
        self.assertTrue(condition_reset.mutable)
        with io.BytesIO() as fd:
            pickle.dump(condition_reset, fd)
            fd.seek(0)
            copied_reset = pickle.load(fd)
        self.assertEqual(copied_reset, condition_reset)
        self.assertTrue(copied_reset.mutable)

    def test_uses_default_arguments(self):
        class MyInstruction(SingletonInstruction):
            def __init__(self, label="my label"):
                super().__init__("my_instruction", 1, 0, [], label=label)

        instruction = MyInstruction()
        self.assertIs(instruction, MyInstruction())
        self.assertFalse(instruction.mutable)
        self.assertIs(instruction.base_class, MyInstruction)
        self.assertEqual(instruction.label, "my label")

        with self.assertRaisesRegex(TypeError, "immutable"):
            instruction.label = None

    def test_suppress_singleton(self):
        # Mostly the test here is that the `class` statement passes; it would raise if it attempted
        # to create a singleton instance since there's no defaults.
        class MyAbstractInstruction(SingletonInstruction, create_default_singleton=False):
            def __init__(self, x):
                super().__init__("my_abstract", 1, 0, [])
                self.x = x

        instruction = MyAbstractInstruction(1)
        self.assertTrue(instruction.mutable)
        self.assertEqual(instruction.x, 1)
        self.assertIsNot(MyAbstractInstruction(1), MyAbstractInstruction(1))

    def test_inherit_singleton(self):
        class ESPMeasure(Measure):
            pass

        measure_base = Measure()
        esp_measure = ESPMeasure()
        self.assertIs(esp_measure, ESPMeasure())
        self.assertIsNot(esp_measure, measure_base)
        self.assertIs(measure_base.base_class, Measure)
        self.assertIs(esp_measure.base_class, ESPMeasure)

        class ESPReset(Reset):
            pass

        reset_base = Reset()
        esp_reset = ESPReset()
        self.assertIs(esp_reset, ESPReset())
        self.assertIsNot(esp_reset, reset_base)
        self.assertIs(reset_base.base_class, Reset)
        self.assertIs(esp_reset.base_class, ESPReset)

    def test_singleton_with_default(self):
        # Explicitly setting the label to its default.
        measure = Measure(label=None)
        self.assertIs(measure, Measure())
        self.assertIsNot(measure, Measure(label="label"))

        reset = Reset(label=None)
        self.assertIs(reset, Reset())
        self.assertIsNot(reset, Reset(label="label"))

    def test_additional_singletons(self):
        additional_inputs = [
            ((1,), {}),
            ((2,), {"label": "x"}),
        ]

        class Discrete(SingletonInstruction, additional_singletons=additional_inputs):
            def __init__(self, n=0, label=None):
                super().__init__("discrete", 1, 0, [], label=label)
                self.n = n

            @staticmethod
            def _singleton_lookup_key(n=0, label=None):  # pylint: disable=arguments-differ
                # This is an atypical usage - in Qiskit standard instruction, the `label` being set
                # not-None should not generate a singleton, so should return a mutable instance.
                return (n, label)

        default = Discrete()
        self.assertIs(default, Discrete())
        self.assertIs(default, Discrete(0, label=None))
        self.assertEqual(default.n, 0)
        self.assertIsNot(default, Discrete(1))

        one = Discrete(1)
        self.assertIs(one, Discrete(1))
        self.assertIs(one, Discrete(1, label=None))
        self.assertEqual(one.n, 1)
        self.assertIs(one.label, None)

        two = Discrete(2, label="x")
        self.assertIs(two, Discrete(2, label="x"))
        self.assertIsNot(two, Discrete(2))
        self.assertEqual(two.n, 2)
        self.assertEqual(two.label, "x")

        # This doesn't match any of the defined singletons, and we're checking that it's not
        # spuriously cached without us asking for it.
        self.assertIsNot(Discrete(2), Discrete(2))

    def test_additional_singletons_copy(self):
        additional_inputs = [
            ((1,), {}),
            ((2,), {"label": "x"}),
        ]

        class Discrete(SingletonInstruction, additional_singletons=additional_inputs):
            def __init__(self, n=0, label=None):
                super().__init__("discrete", 1, 0, [], label=label)
                self.n = n

            @staticmethod
            def _singleton_lookup_key(n=0, label=None):  # pylint: disable=arguments-differ
                return (n, label)

        default = Discrete()
        one = Discrete(1)
        two = Discrete(2, "x")
        mutable = Discrete(3)

        self.assertIsNot(default, default.to_mutable())
        self.assertEqual(default.n, default.to_mutable().n)
        self.assertIsNot(one, one.to_mutable())
        self.assertEqual(one.n, one.to_mutable().n)
        self.assertIsNot(two, two.to_mutable())
        self.assertEqual(two.n, two.to_mutable().n)
        self.assertIsNot(mutable, mutable.to_mutable())
        self.assertEqual(mutable.n, mutable.to_mutable().n)

        # The equality assertions in the middle are sanity checks that nothing got overwritten.

        self.assertIs(default, copy.copy(default))
        self.assertEqual(default.n, 0)
        self.assertIs(one, copy.copy(one))
        self.assertEqual(one.n, 1)
        self.assertIs(two, copy.copy(two))
        self.assertEqual(two.n, 2)
        self.assertIsNot(mutable, copy.copy(mutable))

        self.assertIs(default, copy.deepcopy(default))
        self.assertEqual(default.n, 0)
        self.assertIs(one, copy.deepcopy(one))
        self.assertEqual(one.n, 1)
        self.assertIs(two, copy.deepcopy(two))
        self.assertEqual(two.n, 2)
        self.assertIsNot(mutable, copy.deepcopy(mutable))

    def test_additional_singletons_pickle(self):
        additional_inputs = [
            ((1,), {}),
            ((2,), {"label": "x"}),
        ]

        class Discrete(SingletonInstruction, additional_singletons=additional_inputs):
            def __init__(self, n=0, label=None):
                super().__init__("discrete", 1, 0, [], label=label)
                self.n = n

            @staticmethod
            def _singleton_lookup_key(n=0, label=None):  # pylint: disable=arguments-differ
                return (n, label)

        # Pickle needs the class to be importable.  We want the class to only be instantiated inside
        # the test, which means we need a little magic to make it pretend-importable.
        dummy_module = types.ModuleType("_QISKIT_DUMMY_" + str(uuid.uuid4()).replace("-", "_"))
        dummy_module.Discrete = Discrete
        Discrete.__module__ = dummy_module.__name__
        Discrete.__qualname__ = Discrete.__name__

        default = Discrete()
        one = Discrete(1)
        two = Discrete(2, "x")
        mutable = Discrete(3)

        with unittest.mock.patch.dict(sys.modules, {dummy_module.__name__: dummy_module}):
            # The singletons in `additional_singletons` are statics; their lifetimes should be tied
            # to the type object itself, so if we don't delete it, it should be eligible to be
            # reloaded from and produce the exact instances.
            self.assertIs(default, pickle.loads(pickle.dumps(default)))
            self.assertEqual(default.n, 0)
            self.assertIs(one, pickle.loads(pickle.dumps(one)))
            self.assertEqual(one.n, 1)
            self.assertIs(two, pickle.loads(pickle.dumps(two)))
            self.assertEqual(two.n, 2)
            self.assertIsNot(mutable, pickle.loads(pickle.dumps(mutable)))
