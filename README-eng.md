[🇧🇷 Português](README.md) | 🇺🇸 **English**

<H1> Data Structures Project - Library System (SB) 📚 </H1>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Completed-green?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Trees-BST%20%7C%20RBT%20%7C%20RBT--Intervals-orange?style=flat-square" alt="Trees">
</p>

<p align="center">
  <img src="https://i.postimg.cc/FKSjL5wL/Whats-App-Image-2026-06-08-at-22-47-54.jpg" width="500">
</p>

---

## 📹 Video explaining the project
[YouTube Video](https://youtu.be/vNTnBx7zkx0)

---

## 📝 Description

The **Library System (SB)** is a Python application designed to be fast and user-friendly. Featuring a modern dark mode interface, it was built to ensure fluid navigation and catalog organization, without freezing or unnecessary wait times.

In this new version, the main focus of the system is the **efficient data indexing and searching through tree structures**. To handle different query needs, ID lookup, text search, and loan date conflict detection, the system implements three distinct tree structures: **BST**, **Red-Black Tree (RBT)**, and **Interval RBT**.

Ultimately, the system can instantly index, locate, and verify conflicts across large amounts of books and loans, maintaining a perfect balance between algorithmic efficiency and a simple, pleasant everyday user experience.

## 💡 Technical Highlights - Tree Structures

The major highlight of this update is the Index Module, which uses different tree structures depending on the operation performed in the system:

- **BST (Binary Search Tree):** Implemented as the base structure for indexing books by their number (ID). Guarantees exact lookup in O(log n) average and range queries in O(log n + k). Kept in the project as a reference its O(n) worst-case limitation (sequential ascending insertions) justifies and documents the need for the RBT.

- **RBT (Red-Black Tree):** Replaces the BST as the primary indexing structure, guaranteeing automatic balancing after every insertion and deletion. Maintains the three classic invariants (black root, no consecutive red children, equal black-node count on every root-to-leaf path), maximum height of 2·log₂(n+1), and O(log n) guaranteed in the worst case, including for sequential insertions. Uses a shared `_nil` sentinel node to avoid scattered `None` checks throughout the code.

- **Interval RBT:** Extension of the standard RBT to store loan periods `[start, end]`. Each node maintains an extra field `max_fim` the largest return date in its entire subtree which allows pruning entire branches during overlap searches. Used to check, in O(log n), whether a book is already borrowed during the same period before registering a new loan.

## 🌐 Demonstration

<p align="center">
  <img src="https://i.postimg.cc/Bbp5nTkd/Whats-App-Image-2026-06-08-at-22-48-59.jpg" width="600">
  <br></br>
  <img src="https://i.postimg.cc/T3pjTW0M/Whats-App-Image-2026-06-08-at-22-48-31.jpg" width="600">
  <br></br>
  <img src="https://i.postimg.cc/JncZp3rk/Whats-App-Image-2026-06-08-at-22-50-43.jpg" width="600">
  <br></br>
  <img src="https://i.postimg.cc/BZp2DC7g/Whats-App-Image-2026-06-08-at-22-51-32.jpg" width="600">
</p>

## 🎯 Features

- **ID-Based Search:** The RBT indexes all books by number and performs exact and range lookups in O(log n).
- **Loan Conflict Detection:** The Interval RBT checks in O(log n) whether a book is already borrowed during a given period, using the `max_fim` field to prune irrelevant branches.
- **Catalog Management:** Detailed book registration, including title, author, genre, and stock.
- **Student Registration:** Centralized user control, securely storing enrollment and contact data.
- **Dynamic Editing:** Allows updating information for already registered books and students, keeping the database always up to date.
- **Loan and Popularity Control:** Agile checkout logging, associating the student with the book and automatically counting the number of times it has been borrowed.
- **Returns and Ratings Management:** Automatic loan discharge with an integrated feature for the student to register a 0 to 5-star rating for the returned work.

---

## 💻 Prerequisites

Before running the program, make sure you have the following requirements installed:

**1. Python 3.10 or higher.**

**2. Dependencies:**

- PySide6; and
- qdarktheme.

**3. Operating System: Windows, macOS, or Linux.**

---

## 🚀 Running the Project

**1. Install Python**

Check if you have **Python 3.10 or higher** installed. To do this, follow the steps below:

Open the Terminal (on Windows, use Command Prompt or PowerShell).

Type the following command to check the version:

```bash
python --version
```

**Or**

```bash
python3 --version
```

If you don't have Python 3.10, you can download it [here](https://www.python.org/downloads/).

**2. Clone the Repository**

First, clone the project repository to your machine. Open the terminal and run:

```bash
git clone https://github.com/eda2-2026/G41_Ordenacao_EDA2-2026.1.git
```

**3. Install Dependencies:**

Navigate to the project directory in the terminal and run the following command to install all dependencies:

```bash
pip install -r requirements.txt
```

If the **requirements.txt** file is not present, you can install the dependencies manually.

- **Install Pyside6**

```bash
pip install pyside6
```

- **Install qdarktheme**

```bash
pip install qdarktheme
```

**4. Run the Program**

With the environment configured and dependencies installed, you can now run the system.

```bash
python biblioteca.py
```

Or

```bash
python3 biblioteca.py
```

**⚠️ Note:**
If the code presents any error during execution, verify if all necessary files are present (especially the .json files in the db_files directory).

---

## 🫂 Contributors

| [Camila Cavalcante - 232013944](https://github.com/CamilaSilvaC) | [Luísa Ferreira - 232014807](https://github.com/luisa12ll) |
| :---: | :---: |
| <div align="center"><img src="https://github.com/CamilaSilvaC.png" alt="camila" width="400"></div> | <div align="center"><img src="https://github.com/luisa12ll.png" alt="luisa" width="400"></div> |