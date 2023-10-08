# -*- coding: utf-8 -*-
"""iccad-prod-workflow-doc.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Nn8GJ0i0LP2cqfw0mxqUYN7pcmtlfmXz

# Code for Estimating the Ground State Energy of the Hydroxyl Cation using BQSKit

This Jupyter notebook walks through the workflow of circuit synthesis and evaluation to estimate the ground state energy of the hydyoxyl radical. Note that this script will save a QASM string in your current working directory due to how the compilation process is implemented.

This notebook is heavily inspired by the provided [example code](https://github.com/qccontest/QC-Contest-Demo/blob/main/examplecode.ipynb) and [noise model code](https://github.com/qccontest/QC-Contest-Demo/blob/main/NoiseModel_and_SystemModel.ipynb).

## Basic Installation
Install required packages.
"""

# Used for modeling the hydroxyl radical
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper,ParityMapper,QubitConverter

# Used for VQE
from qiskit.algorithms.minimum_eigensolvers import VQE
from qiskit.algorithms.optimizers import SLSQP
from qiskit_aer.primitives import Estimator
from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD
from qiskit.algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

# Used for transpilation and circuit modeling in Qiskit
import numpy as np
import pylab
import qiskit.providers
from qiskit import Aer,pulse, QuantumCircuit, transpile
from qiskit.utils import QuantumInstance, algorithm_globals
import time

# Used for circuit synthesis and optimization
from bqskit import compile, Circuit

# Used for converting the provided Hamiltonian file into
# a usable Pauli representation
from qiskit.quantum_info import SparsePauliOp

# Used for noise modeling
from qiskit.providers.aer.noise import NoiseModel
import qiskit.providers.aer.noise as noise

# Used for quantum hardware backend
from qiskit.providers.fake_provider import *

# Used for reading noise model files
import pickle

# Define a function for parsing the Hamiltonian string into a list of
# Pauli strings.
def parse_hamiltonian(content: str):
    """
    Parses the input Hamiltonian string and returns a list of Pauli strings
    padded for a circuit with 27 qubits with their coefficients.

    Args:
    content (str): The string representation of the Hamiltonian to parse.
    It is assumed that the file contains one Pauli coefficient and string per
    line, and each line is of the format "<coeff> * <pauli_string>".

    Returns:
    A list of tuples representing a list of the Pauli coefficients and strings.
    Each tuple is of the form (<coeff>, <pauli_string>), where <coeff> is a
    floating point number representing the coefficient, and <pauli_string> is
    a string of length 27 for a circuit with 27 physical qubits.
    """

    # Initializing the list to hold the parsed Pauli operators and their coefficients
    pauli_list = []

    # Splitting the content into lines and parsing each line
    for line in content.splitlines():
        # Removing the '+' symbol and splitting each line into coefficient and operator parts
        parts = line.replace('+', '').replace('- ', '-').split(' * ')

        # If the line is correctly formatted, it should have exactly two parts
        if len(parts) == 2:
            try:
                # The first part is the coefficient
                coefficient = float(parts[0])
                # The second part is the operator string
                # Prepend 15 I's to fit to FakeMontreal hardware backend
                operator = "I" * 15 + parts[1]

                # Appending the parsed operator and coefficient to the list
                pauli_list.append((operator, coefficient))
            except ValueError:  # Handle lines that cannot be parsed correctly
                print('Error: cannot parse this Pauli string:', parts)

    return pauli_list

def obtain_qmolecule():
    """
    ## Generate Hamiltonian and Pauli String

    The code sets up PySCF to generate the hamiltonian of the hydroxyl cation with the basis function as 'sto3g' to fit the spin orbital, and then uses the JordanWignerMapper to map the Fermionic terms to Pauli strings.

    Note: this code reads the Hamiltonian from the 'hamiltonian_file_path' when it needs to evaluate the correctness of the circuit.
    """

    # Define a string representing a simplified molecular structure of Alanine,
    # specifying the coordinates of Oxygen (O) and Hydrogen (H) atoms.
    ultra_simplified_ala_string = """
    O 0.0 0.0 0.0
    H 0.45 -0.1525 -0.8454
    """

    # Create a PySCF Driver for the hydroxyl cation using the 'sto3g' basis
    # function to fit the spin orbital.
    driver = PySCFDriver(
        atom=ultra_simplified_ala_string.strip(),
        basis='sto3g',
        charge=1,
        spin=0,
        unit=DistanceUnit.ANGSTROM
    )

    # Obtain a qmolecule containing molecular information generated by the driver.
    qmolecule = driver.run()

    # Obtain the Hamiltonian.
    hamiltonian = qmolecule.hamiltonian
    coefficients = hamiltonian.electronic_integrals
    # print(coefficients.alpha)

    # Obtain the second quantized operations from the Hamiltonian.
    second_q_op = hamiltonian.second_q_op()

    # Create an instance of the JordanWignerMapper.
    mapper = JordanWignerMapper()

    # Create a converter from fermionic operators to qubit operators,
    # using the Jordan Wigner Mapper. Do not reduce the number
    # of required qubits by two.
    converter = QubitConverter(mapper=mapper, two_qubit_reduction=False)

    # Convert the second quantized operator (second_q_op) to a qubit operator (qubit_op).
    qubit_op = converter.convert(second_q_op)

    return qmolecule

def obtain_ref_energy(qmolecule):
    """## Obtain Reference Energy using Classical Simulation
    We use the classical minimum eigensolver to obtain a reference energy of the hydroxyl radical.
    """

    # Create a solver for the ground state energy, which applies the
    # Jordan-Wigner transformation and uses a classical eigensolver.
    solver = GroundStateEigensolver(
        JordanWignerMapper(),
        NumPyMinimumEigensolver(),
    )

    # Obtain the reference energy.
    result = solver.solve(qmolecule)
    print(result.computed_energies)

    # Print the nuclear repulsion energy.
    print(result.nuclear_repulsion_energy)

    # Obtain the ground state energy, which is the sum of the computed
    # energies and the nuclear repulsion energy.
    ref_value = result.computed_energies + result.nuclear_repulsion_energy
    ref_value_float = ref_value[0]
    print(ref_value_float)

    # print(qmolecule.num_spatial_orbitals)
    # print(qmolecule.num_particles)
    # print(mapper)

    return ref_value_float

def obtain_parameterized_ansatz(qmolecule, seed, shots, seed_transpiler):
    """
    ### Obtain parameterized UCCSD Ansatz using VQE
    This step of the code obtains the parameterized UCCSD ansatz by running VQE.
    """

    # Create an instance of the UCCSD ansatz using the properties of
    # the hydroxyl radical.
    ansatz = UCCSD(
        qmolecule.num_spatial_orbitals,
        qmolecule.num_particles,
        JordanWignerMapper(),
        initial_state=HartreeFock(
            qmolecule.num_spatial_orbitals,
            qmolecule.num_particles,
            JordanWignerMapper(),
        ),
    )

    # Create an estimator for the ground state energy of the hydroxyl radical.
    # Use the seed and specified number of shots.
    estimator = Estimator(
        backend_options = {
            'method': 'statevector',
            'device': 'CPU'
            # 'noise_model': noise_model
        },
        run_options = {
            'shots': shots,
            'seed': seed,
        },
        transpile_options = {
            'seed_transpiler':seed_transpiler
        }
    )

    # Create a VQE solver.
    vqe_solver = VQE(estimator, ansatz, SLSQP())
    # Set an initial point for the optimization.
    vqe_solver.initial_point = [0.0] * ansatz.num_parameters

    # Computes the ground state energy using a simulator
    # and optimizes the parameters for the UCCSD ansatz
    # through VQE.
    start_time = time.time()
    calc = GroundStateEigensolver(JordanWignerMapper(), vqe_solver)
    res = calc.solve(qmolecule)
    end_time = time.time()
    # print(res)

    # Obtain the optimal parameters for the UCCSD ansatz from VQE.
    optimal_point = res.raw_result.optimal_point
    # print(optimal_point)

    # Obtain the parameterized UCCSD ansatz as a result of VQE.
    optimized_ansatz = vqe_solver.ansatz.bind_parameters(optimal_point)
    optimized_ansatz_qasm = optimized_ansatz.qasm()

    return optimized_ansatz_qasm

def compile_circ_bqskit(optimized_ansatz_qasm, seed, noisemodel_name):
    """### Transpile the Parameterized UCCSD ansatz and perform circuit synthesis using BQSKit
    We then transpile the parameterized UCCSD ansatz on Qiskit's QASM simulator to obtain a circuit with one and two qubit gates, and then perform BQSKit with an optimization level of 3 (for fine-tuning of gate parameters).
    """

    # Obtain a Qiskit representation of the parameterized ansatz.
    circuit = QuantumCircuit.from_qasm_str(optimized_ansatz_qasm)

    # Use the QASM simulator backend.
    backend = Aer.get_backend('qasm_simulator')

    # Transpile the circuit on the simulator with optimization level 0, as we
    # only want to obtain a circuit with one and two qubit gates.
    transpiled_circuit = transpile(circuit, backend, optimization_level=0, seed_transpiler=seed)

    # transpiled_circuit.depth()

    # Set a base file name to save an intermediate QASM file.
    base_ansatz_filename = 'UCCSD_VQE_ansatz_seed' + str(seed) + '_' + noisemodel_name

    # Write the circuit in QASM form to the file. This is necessary for
    # BQSKit to read in the circuit.
    with open(base_ansatz_filename + '_transpiled' + '.qasm', 'w') as file:
        file.write(transpiled_circuit.qasm())

    # Obtain a BQSKit representation of the transpiled circuit.
    bqskit_rep_circuit = Circuit.from_file(base_ansatz_filename + '_transpiled' + '.qasm')

    # Compile the circuit using BQSKit, with the optimization level as 3.
    compiled_circuit = compile(bqskit_rep_circuit, optimization_level=3, seed=seed)

    # print(compiled_circuit.depth)

    return compiled_circuit

def evaluate_circuit(transpiled_circuit_montreal, hamiltonian_file_path, noisemodel_path, shots, seed, qmolecule, ref_value_float):
    # Read in the Hamiltonian as a string.
    with open(hamiltonian_file_path, 'r') as file:
        hamiltonian_str = file.read()

    # Obtain the observable as a Sparse Pauli Operator
    observable = SparsePauliOp.from_list(parse_hamiltonian(hamiltonian_str))
    print(len(observable))
    print(f">>> Observable: {observable.paulis}")

    # Read in the noise model
    with open(noisemodel_path, 'rb') as file:
        noise_model = pickle.load(file)

    # Initialize a container for the noise model
    noise_model1 = noise.NoiseModel()

    # Parameterize the noise model object with the specified noise model
    noise_modelreal = noise_model1.from_dict(noise_model)

    # noise_modelreal

    # Create an estimator for the ground state energy, using the specified shots
    # and the noise model.
    # Skip transpilation as we've already transpiled our circuit onto the system
    # model.
    estimator = Estimator(
        backend_options = {
            'method': 'statevector',
            'device': 'CPU',
            'noise_model': noise_modelreal
        },
        run_options = {
            'shots': shots,
            'seed': seed,
        },
        skip_transpilation=True
    )

    # Run the estimator to obtain the ground state energy.
    job = estimator.run(transpiled_circuit_montreal,observable)
    result = job.result()
    print(f">>> {result}")

    # Set the computed energy and the nuclear repulsion energy.
    res_computeden = result.values[0]
    # The nuclear repulsion energy is a constant based on the input
    # molecule.
    res_nuc_repulen = qmolecule.nuclear_repulsion_energy

    # print(res_computeden)
    # print(res_nuc_repulen)

    # Compute the accuracy between the observed energy and the reference energy.
    result_energy = res_computeden + res_nuc_repulen
    accuracy_score = (1 - abs((result_energy - ref_value_float) / ref_value_float)) * 100
    print("Accuracy Score: %f%%" % (accuracy_score))

    return accuracy_score

def perform_workflow(noisemodel_name, seed, shots=2852):
    """
    Performs the entire circuit generation and synthesis workflow for a given
    noise model and seed.

    Args:
    noisemodel_name (str): The name of the noise model to use when evaluating
    the resulting ansatz. noisemodel_name MUST be one of 'fakecairo.pkl', 'fakekolkata.pkl',
    and 'fakemontreal.pkl'.
    seed (int): The seed to use throughout the workflow.
    shots (int): The number of shots to use throughout the workflow. Default is 2852.

    Returns:
    A float representing the accuracy score for the given noise model and seed.
    """

    # Set the seed used throughout the workflow.
    seed = seed
    algorithm_globals.random_seed = seed
    seed_transpiler = seed

    # Set the number of shots used throughout the workflow.
    shots = shots

    # Sets the noise model name, which is used for saving a QASM file
    # in the current working directory.
    noisemodel_name = noisemodel_name

    # Set the noise model used in the workflow.
    noisemodel_path = './NoiseModel/' + noisemodel_name + '.pkl'

    # Sets the hamiltonian used in the workflow.
    hamiltonian_file_path = './Hamiltonian/OHhamiltonian.txt'

    qmolecule = obtain_qmolecule()

    ref_value_float = obtain_ref_energy(qmolecule)

    """## Construct Ansatz using VQE and Circuit Synthesis
    At this step, we first perform VQE on the UCCSD ansatz to obtain a parameterized circuit. We then transpile the circuit so it has one and two qubit gates, and proceed to circuit synthesis with BQSKit.
    """

    optimized_ansatz_qasm = obtain_parameterized_ansatz(qmolecule, seed, shots, seed_transpiler)

    compiled_circuit = compile_circ_bqskit(optimized_ansatz_qasm, seed, noisemodel_name)

    """## Circuit Evaluation
    We now evaluate the circuit with the provided Hamiltonian and use Qiskit's Estimator to estimate the ground state energy.
    """

    # Initialize the system model
    system_model = FakeMontreal()

    # Obtain a Qiskit representation of the BQSKit compiled circuit
    compiled_circ_qiskit = QuantumCircuit.from_qasm_str(compiled_circuit.to('qasm'))

    # compiled_circ_qiskit.draw()

    layout = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    # Transpile the circuit with the above layout on the system model.
    transpiled_circuit_montreal = transpile(compiled_circ_qiskit, backend=system_model, seed_transpiler=seed, initial_layout=layout)

    accuracy_score = evaluate_circuit(transpiled_circuit_montreal, hamiltonian_file_path, noisemodel_path, shots, seed, qmolecule, ref_value_float)

    """### Obtain the Duration of the Final Circuit
    Here, we use the 'pulse' module from Qiskit to obtain the duration of the
    quantum circuit in terms of the time resolution of the system model.
    """

    from qiskit import pulse

    # Build a pulse schedule for the quantum circuit on the specified
    # system model
    with pulse.build(system_model) as my_program1:
        with pulse.transpiler_settings(optimization_level=0):
            pulse.call(transpiled_circuit_montreal)

    # Print the duration of the quantum circuit
    print(my_program1.duration)

    # Print the final transpiled circuit.
    print(transpiled_circuit_montreal.qasm())

    return accuracy_score

