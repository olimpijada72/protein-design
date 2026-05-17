# Explanation of Theoretical Aspects 

## 1. Protein Biology Fundamentals

### 1.1. What is Protein and What is it Made of?
Proteins are biological macromolecules composed of amino acid chains whose three-dimensional structure determines their function. In computational protein design, proteins are typically represented either as amino acid sequences or as 3D atomic coordinates, depending on the modeling task.

Each has amino acid has:
- **Backbone**: Same structure in all amino acids (–NH₂, –COOH).
- **Side chain (R group)**: Gives each amino acid its chemical properties (hydrophobic, polar, charged).
The sequence of amino acids determines the protein’s shape and function.

![protein diagram](/figures/protein_diagram.png)


An amino acid residue is the portion of an amino acid that remains after it has formed a peptide bond with other amino acids in a protein or peptide chain, losing a molecule of water in the process; it's the fundamental building block of proteins, retaining the unique

The alpha (α) carbon in proteins is the central carbon atom in an amino acid, bonded to the amino group (–NH₂), carboxyl group (–COOH), a hydrogen atom, and the variable side chain (R-group) that defines the amino acid's identity, making it the crucial backbone point for protein structure, folding, and function. In the protein chain, it connects the carbonyl carbon of one residue to the nitrogen of the next, forming the polypeptide backbone. 


![peptide bond](/figures/peptide_bond_diagram.png)


### 1.2. Protein Structure
There are 4 different structural levels at which proteins are observed

![Protein structures](/figures/protein_structures.png)

1) Primary - The Sequence
    - Simply the **sequence of amino acids** written from the **N terminus** (amino end) to the **C terminus** (Carboxyl end)
    - Determines everything about the protein’s final shape and function. Even a single amino acid change can cause major effects (e.g., sickle cell anemia from a single substitution in hemoglobin).

2. Secondary Structure — Local Folding Patterns
    - Localized conformation of the cain, i.e. **the folding pattern over a few dozen amino acid residues**
    - Provides structural stability and scaffolding for the protein’s shape.
    - Main types:
        - **α-helix** - A right-handed coil stabilized by hydrogen bonds every 4 residues (keratin in hair).
        - **β-sheet** — Strands linked side-by-side; can be parallel or antiparallel (silk fibroin).

3. Tertiary Structure — Overall 3D Shape
    - The full 3D arrangement of the entire polypeptide chain, including how secondary structures pack together.
    - Defines the protein’s active sites and binding surfaces.

4. Quaternary Structure — Multiple Subunits
    - The arrangement of multiple polypeptide chains (subunits) into one functional protein complex.
    - Allows cooperative behavior, regulation, and complex functions.
    - Example: Hemoglobin — 4 subunits work together to transport oxygen.


### 1.3. Key Functional Categories
- Enzymes — Catalyze biochemical reactions.
- Transport proteins — Hemoglobin, ion channels.
- Signaling proteins — Hormones, receptors.
- Structural proteins — Actin, collagen.
- Defense proteins — Antibodies.

### 1.4. CATH Classification System
CATH (Class – Architecture – Topology – Homologous superfamily) is a hierarchical classification system that organizes protein domains based on their **3D structural features** and **evolutionary relationships.** There are 4 levels:
1. **Class (C)**
    - Broadest category, based on **secondary structure composition.**
    - Example:
        - Mainly α (helices dominate)
        - Mainly β (sheets dominate) 
        - α–β mixed
2. **Architecture (A)**
    - **Arrangement of secondary structures in 3D space**, ignoring connectivity.
    - Example: β-barrel, α-sandwich, α–β horseshoe.
    - Captures the *overall shape of the domain.*
3. **Topology (T)**
    - Also called **fold.**
    - Includes **connectivity/order of secondary structures.**
    - Example: TIM barrel fold (α/β-barrel).
    - Domains with the same topology often evolved from a common ancestor.
4. **Homologous superfamily (H)**
    - Groups domains with **clear evidence of evolutionary relationship.**
    -  Members share similar structures and often related functions.

![CATH system](/figures/cath_system.png)


### 1.5. Immungolobulin (Ig)
- Immunoglobulin is a protein family wiht the **immunoglobulin fold** (β-sandwich of antiparallel β-strands)
- **Antibodies are speciliazed immunoglobulins** produced by B cells that bind antigens
- All antibodies are immunoglobulins, but not all immunoglobulins act as antibodies. Think of immunoglobulin as the “category” (like *dog*), and antibody as a specific “job” some of those proteins have (like *guide dog*). All guide dogs are dogs, but not all dogs are guide dogs.

![immunoglobulin diagram.](/figures/immunoglobulin_diagram.png)

Immunoglobulin-like folds correspond to 2.60.40 in the CATH system:
- 2 → Class: Mainly β
- 60 → Architecture: β-barrel
- 40 → Topology (Fold family): Immunoglobulin-like β-sandwich
- So, 2.60.40 = the Ig-like β-sandwich fold.

## 2. Protein Representation in Machine Learning
- sequences
- one-hot encoding
- embeddings
- structural graphs
- coordinate systems
- Explain the different file formats used in this project (fasta, pdb, etc)

## 3. How proteina Works?
- inverse folding
- structure-conditioned sequence generation
- backbone generation
- intuition
- diffusion vs flow matching
- why Proteina works

## 4. How ProteinMPNN Works?
- graph representation
- message passing
- autoregressive decoding

## 5. How CATHe2 Works?
- protein language models
- fold classification
- embeddings

## 6. Pipeline Integration
how all components connect