import unittest
import qiskit
from qiskit import QuantumCircuit, Aer
from VQD import VQD
from utils import classical_solver
from qiskit.aqua.operators import Z,I



class TestVQD(unittest.TestCase): 

    def setUp(self):

        optimizer = qiskit.aqua.components.optimizers.COBYLA()
        backend = qiskit.Aer.get_backend('qasm_simulator')
        self.Algo = VQD(n_qubits=2,
                        n_excited_states=1,
                        beta=1.,
                        optimizer=optimizer,
                        backend=backend)
        self.Algo.run(verbose=0)
        hamiltonian = 1/2*((Z^I) + (Z^Z))
        self.eigenvalues = classical_solver(hamiltonian)
        
    
    def test_energies(self): 
        want = self.eigenvalues[0]
        got = self.Algo.energies[0]
        decimalPlace = 1
        message = "VQD not working for the ground state of 1/2*((Z^I) + (Z^Z))"
        self.assertAlmostEqual(want, got, decimalPlace, message)
        want = self.eigenvalues[1]
        got = self.Algo.energies[1]
        message = "VQD not working for the first excited state of 1/2*((Z^I) + (Z^Z))"
        self.assertAlmostEqual(want, got, decimalPlace, message)
    

if __name__== "__main__":
    unittest.main(argv=[''], verbosity=2, exit=False);