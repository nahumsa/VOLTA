####################
## Helper imports ##
####################
import numpy as np
from typing import Union

import sys
sys.path.append('../')

####################
## Qiskit imports ##
####################
import qiskit
from qiskit import QuantumCircuit
from qiskit.aqua.operators import OperatorBase, ListOp, PrimitiveOp, PauliOp
from qiskit.aqua.operators import I, X, Y, Z
from qiskit.circuit.library import TwoLocal
from qiskit.aqua.components.optimizers import Optimizer
from qiskit.aqua import QuantumInstance
from qiskit.providers import BaseBackend

###################
## Local imports ##
###################
from VOLTA.Observables import sample_hamiltonian
from VOLTA.SWAPTest import measure_swap_test, measure_dswap_test

################
## begin code ##
################

class VQD(object):
    """Variational Quantum Deflation algorithm class.

    Based on https://arxiv.org/abs/1805.08138 

    """
    def __init__(self, 
                 hamiltonian: Union[OperatorBase, ListOp, PrimitiveOp, PauliOp],
                 ansatz: QuantumCircuit,
                 n_excited_states: int, 
                 beta: float,
                 optimizer: Optimizer, 
                 backend: Union[BaseBackend, QuantumInstance],
                 dswap: bool=False,
                 num_shots: int=10000,
                 debug: bool=False):
        """Initialize the class.

        Args:
            hamiltonian (Union[OperatorBase, ListOp, PrimitiveOp, PauliOp]): Hamiltonian 
            constructed using qiskit's aqua operators.
            ansatz (QuantumCircuit): Anstaz that you want to run VQD.
            n_excited_states (int): Number of excited states that you want to find the energy
            if you use 0, then it is the same as using a VQE.
            beta (float): Strenght parameter for the swap test.
            optimizer (qiskit.aqua.components.optimizers.Optimizer): Classical Optimizers 
            from aqua components.
            backend (Union[BaseBackend, QuantumInstance]): Backend for running the algorithm.
            num_shots (int): Number of shots. (Default: 10000)
        """
        
        # Input parameters
        self.hamiltonian = hamiltonian        
        self.n_qubits = hamiltonian.num_qubits
        self.optimizer = optimizer
        self.backend = backend
        self.NUM_SHOTS = num_shots
        self.BETA = beta
        self.dswap = dswap
        
        # Helper Parameters
        self.n_excited_states = n_excited_states + 1
        self.ansatz = ansatz
        self.n_parameters = self._get_num_parameters
        self._debug = debug

        # Logs
        self._states = []
        self._energies = []

    @property
    def energies(self):
        """ Returns a list with energies.

        Returns:
            list: list with energies
        """
        return self._energies
    
    @property
    def states(self):
        """ Returns a list with states associated with each energy.

        Returns:
            list: list with states.
        """
        return self._states

    @property
    def _get_num_parameters(self) -> int:
        """Get the number of parameters in a given ansatz.

        Returns:
            int: Number of parameters of the given ansatz.
        """
        return len(self.ansatz.parameters)

    def _apply_varform_params(self, params: list):
        """Get an hardware-efficient ansatz for n_qubits
        given parameters.
        """

        # Define variational Form
        var_form = self.ansatz

        # Get Parameters from the variational form
        var_form_params = sorted(var_form.parameters, key=lambda p: p.name)

        # Check if the number of parameters is compatible
        assert len(var_form_params) == len(params), "The number of parameters don't match"

        # Create a dictionary with the parameters and values
        param_dict = dict(zip(var_form_params, params))

        # Assing those values for the ansatz
        wave_function = var_form.assign_parameters(param_dict)

        return wave_function
    
    
    def cost_function(self, params:list) -> float:
        """Evaluate the cost function of VQD.

        Args:
            params (list): Parameter values for the ansatz.

        Returns:
            float: Cost function value.
        """
        # Define Ansatz
        qc = self._apply_varform_params(params)

        # Hamiltonian
        hamiltonian_eval = sample_hamiltonian(hamiltonian=self.hamiltonian, 
                                             ansatz=qc, 
                                             backend=self.backend)

        # Fidelity
        fidelity = 0.
        if len(self.states) != 0:
            for state in self.states:
                if self.dswap:
                    swap = measure_dswap_test(qc, state, self.backend, self.NUM_SHOTS)
                else:
                    swap = measure_swap_test(qc, state, self.backend, self.NUM_SHOTS)
                fidelity += swap
                
                if self._debug:
                    print(fidelity)

        # Get the cost function
        cost = hamiltonian_eval + self.BETA*fidelity
        
        return cost

    def optimizer_run(self):
        
        # Random initialization
        params = np.random.rand(self.n_parameters)

        optimal_params, energy, n_iters = self.optimizer.optimize(num_vars=self.n_parameters, 
                                                                  objective_function=self.cost_function, 
                                                                  initial_point=params)
        
        # Logging the energies and states
        # TODO: Change to an ordered list.
        
        self._energies.append(energy)
        self._states.append(self._apply_varform_params(optimal_params))
    
    def _reset(self):
        """Resets the energies and states helper variables.
        """

        self._energies = []
        self._states = []

    def run(self, verbose: int=1):
        
        self._reset()
        
        for i in range(self.n_excited_states):
            
            if verbose == 1:
                print(f"Calculating excited state {i}")
            
            self.optimizer_run()


##############        
## End code ##
##############