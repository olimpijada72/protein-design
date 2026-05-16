# Explanation of Theoretical Aspects 

## Biology Knowledge Prerequisites

### What is Protein and What is it Made of?
Proteins are large, complex molecules made from chains of amino acids linked by peptide bonds. There are 20 standard amino acids (plus a few rare ones like selenocysteine).

Each has amino acid has:
- **Backbone**: Same structure in all amino acids (–NH₂, –COOH).
- **Side chain (R group)**: Gives each amino acid its chemical properties (hydrophobic, polar, charged).
The sequence of amino acids determines the protein’s shape and function.

![protein diagram](/figures/protein_diagram.png)


An amino acid residue is the portion of an amino acid that remains after it has formed a peptide bond with other amino acids in a protein or peptide chain, losing a molecule of water in the process; it's the fundamental building block of proteins, retaining the unique

The alpha (α) carbon in proteins is the central carbon atom in an amino acid, bonded to the amino group (–NH₂), carboxyl group (–COOH), a hydrogen atom, and the variable side chain (R-group) that defines the amino acid's identity, making it the crucial backbone point for protein structure, folding, and function. In the protein chain, it connects the carbonyl carbon of one residue to the nitrogen of the next, forming the polypeptide backbone. 


![peptide bond](/figures/peptide_bond_diagram.png)


### Protein Structure
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


### Key Functional Categories
- Enzymes — Catalyze biochemical reactions.
- Transport proteins — Hemoglobin, ion channels.
- Signaling proteins — Hormones, receptors.
- Structural proteins — Actin, collagen.
- Defense proteins — Antibodies.

### CATH Classification System
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


### Immungolobulin (Ig)
- Immunoglobulin is a protein family wiht the **immunoglobulin fold** (β-sandwich of antiparallel β-strands)
- **Antibodies are speciliazed immunoglobulins** produced by B cells that bind antigens
All antibodies are immunoglobulins, but some immunoglobulins function in other immune signaling pathways without directly neutralizing antigens.
- All antibodies are immunoglobulins, but not all immunoglobulins act as antibodies. Think of immunoglobulin as the “category” (like *dog*), and antibody as a specific “job” some of those proteins have (like *guide dog*). All guide dogs are dogs, but not all dogs are guide dogs.

![immunoglobulin diagram.](/figures/immunoglobulin_diagram.png)

Immunoglobulin-like folds correspond to 2.60.40 in the CATH system:
- 2 → Class: Mainly β
- 60 → Architecture: β-barrel
- 40 → Topology (Fold family): Immunoglobulin-like β-sandwich
- So, 2.60.40 = the Ig-like β-sandwich fold.

## How proteina Works?


## How ProteinMPNN Works?


## How CATHe2 Works?

