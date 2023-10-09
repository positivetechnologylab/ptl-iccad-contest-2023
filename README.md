# Generating Low-Depth Quantum Variational Circuits for the Hydroxyl Cation to Attain High Fidelity on NISQ Computers

This is the Positive Technology Lab at Rice University's submission for the [2023 Quantum Computing for Drug Discovery Challenge at ICCAD](https://qccontest.github.io/QC-Contest/index.html).

## Usage
1. In your terminal, run `git clone https://github.com/positivetechnologylab/ptl-iccad-contest-2023.git` to clone the repository.
2. Run `cd ptl-iccad-contest-2023`.
3. Create a virtual environment if necessary, and run `pip install -r requirements.txt` to install the requirements.
4. Run `python main.py <noisemodel_name> <seed> [shots]>`, where
    - `noisemodel_name` is either `fakecairo`, `fakekolkata`, or `fakemontreal`
    - `seed` is an integer representing the seed to use
    - `shots` is an integer representing the number of shots used
5. To interpret the results, there is a line in the output with the following format: `Accuracy Score: __%`. This is the accuracy score for that particular run.

## Requirements
The requirements and specific versions are provided in `requirements.txt`.

## Notebook Usage
1. In your terminal, run `git clone https://github.com/positivetechnologylab/ptl-iccad-contest-2023.git` to clone the repository.
2. Run `cd ptl-iccad-contest-2023`.
3. Create a virtual environment if necessary, and run `pip install -r requirements.txt` to install the requirements.
4. Navigate to the 'icacd_prod_workflow_doc_ipynb' notebook.
5. In the section below **Initialize Configuration Variables**, specify the seed to use in the 'seed' variable, and the name of the noise model to use ('fakecairo', 'fakekolkata', or 'fakemontreal').
6. Run all cells in the notebook.
7. One of the cells will print out the accuracy score in the following format: `Accuracy Score: __%`. This is the accuracy score for that particular run.

## Notes
We'd like to note that our Python workflow incorporates the Qiskit estimator for evaluating the quantum circuits, inspired from the provided [Noise Model and System Model code](https://github.com/qccontest/QC-Contest-Demo/blob/main/NoiseModel_and_SystemModel.ipynb).

## For Developers
If you would like to customize the workflow, the `iccad_prod_workflow_doc.py` files provides Python functions that break down parts of the workflow and can be modified to suit your needs. In particular, `obtain_parameterized_ansatz` runs VQE and returns the parameterized UCCSD ansatz, `compile_circ_bqskit` compiles an input circuit using our BQSKit workflow, and `evaluate_circuit` uses the Qiskit Estimator class to evaluate a transpiled circuit on the FakeMontreal() backend.

## Repository Structure
- [**`FinalCircuits/`**](FinalCircuits/): Directory containing three QASM files for the three noise models, prefixed with ’FakeCairo’, ’FakeKolkata’, and ’FakeMontreal’, for the Cairo, Kolkata, and Montreal noise models, respectively. The accuracies and seeds are also provided in the name of the files, for reproducibility.
- [**`Hamiltonian/`**](Hamiltonian/): Directory containing a file Hamiltonian.txt that is used as the Hamiltonian of the input hydroxyl radical. This directory is identical to the provided [Hamiltonian directory](https://github.com/qccontest/QC-Contest-Demo/tree/main/Hamiltonian).
- [**`NoiseModel/`**](NoiseModel/): Directory containing the noise models used by the code for evaluating the accuracy of the quantum circuits. This directory is identical to the provided [Noise Model directory](https://github.com/qccontest/QC-Contest-Demo/tree/main/NoiseModel).
- [**`README.md`**](README.md): Repository readme with setup and execution instructions.
- [**`iccad_prod_workflow_doc.ipynb`**](iccad_prod_workflow_doc.ipynb): Tutorial notebook for an end-to-end workflow for our circuit synthesis and optimization workflow.
- [**`iccad_prod_workflow_doc.py`**](iccad_prod_workflow_doc.py): Python file containing functions used in our workflow.
- [**`main.py`**](main.py): Python file to be run from the command line to execute our workflow programmatically.
- [**`requirements.txt`**](requirements.txt): Requirements to be installed before running the Python scripts. These include the Qiskit, Qiskit Nature, Qiskit Aer, and BQSKit Python libraries.
- [**`PTL_ICCAD_Design.pdf`**](PTL_ICCAD_Design.pdf): The design document describing our solution to the contest problem in detail.

## Copyright
Copyright © 2023 Positive Technology Lab. All rights reserved. For permissions, contact ptl@rice.edu.