# Generating Low-Depth Quantum Variational Circuits for the Hydroxyl Cation to Attain High Fidelity on NISQ Computers

This is the Positive Technology Lab at Rice University's submission for the [2023 Quantum Computing for Drug Discovery Challenge at ICCAD](https://qccontest.github.io/QC-Contest/index.html).

## Usage
1. Navigate to the 'icacd_prod_workflow_doc_ipynb' notebook.
2. In the section below **Initialize Configuration Variables**, specify the seed to use in the 'seed' variable, and the name of the noise model to use ('fakecairo', 'fakekolkata', or 'fakemontreal').
3. Run all cells in the notebook.

## Requirements
1. Qiskit, for loading Quantum circuits and for ground state estimation algorithms
2. Qiskit Nature, for modelling the hydroxyl radical and the ground state eigensolver
3. BQSKit, for performing circuit synthesis and optimization on the quantum circuit
4. Qiskit Aer, for estimating the ground state energy