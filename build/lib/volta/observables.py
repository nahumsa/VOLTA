from typing import Union
import qiskit
import numpy as np
from qiskit.utils.backend_utils import is_aer_provider
from qiskit.opflow import (
    CircuitSampler,
    ExpectationFactory,
    CircuitStateFn,
    StateFn,
)


def sample_hamiltonian(
    hamiltonian: qiskit.opflow.OperatorBase,
    backend: Union[qiskit.providers.BaseBackend, qiskit.utils.QuantumInstance],
    ansatz: qiskit.QuantumCircuit,
) -> float:
    """Samples a hamiltonian given an ansatz, which is a Quantum circuit
    and outputs the expected value given the hamiltonian.

    Args:
        hamiltonian (qiskit.opflow.OperatorBase): Hamiltonian that you want to get the
        expected value.
        backend (Union[qiskit.providers.BaseBackend, qiskit.utils.QuantumInstance]): Backend
        that you want to run.
        ansatz (qiskit.QuantumCircuit): Quantum circuit that you want to get the expectation
        value.

    Returns:
        float: Expected value
    """
    if qiskit.utils.quantum_instance.QuantumInstance == type(backend):
        sampler = CircuitSampler(backend, param_qobj=is_aer_provider(backend.backend))
    else:
        sampler = CircuitSampler(backend)

    expectation = ExpectationFactory.build(operator=hamiltonian, backend=backend)
    observable_meas = expectation.convert(StateFn(hamiltonian, is_measurement=True))

    ansatz_circuit_op = CircuitStateFn(ansatz)

    expect_op = observable_meas.compose(ansatz_circuit_op).reduce()
    sampled_expect_op = sampler.convert(expect_op)

    return np.real(sampled_expect_op.eval())
