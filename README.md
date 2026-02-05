# Memory Hierarchy Simulator 🧠

A comprehensive simulation of computer memory hierarchy designed for the **Computer Architecture** course. This project visualizes how data moves between CPU, Caches (L1, L2, L3), Main Memory (RAM), and Secondary Storage (Disk).

## 🚀 Features

* **Multi-Level Cache Simulation:** Simulates L1, L2, and L3 caches with configurable sizes and latencies.
* **Replacement Policies:** Includes 5 algorithms:
    * LRU (Least Recently Used)
    * LFU (Least Frequently Used)
    * FIFO (First-In, First-Out)
    * MRU (Most Recently Used)
    * Random
* **Interactive GUI:** Built with `tkinter` for easy configuration and real-time visualization.
* **Performance Analysis:** Calculates AMAT (Average Memory Access Time), Hit/Miss rates, and generates graphical charts using `matplotlib`.
* **Workload Generation:** Simulates real-world access patterns (Locality of Reference) using Gaussian distribution.

## 🛠️ Built With

* **Python 3.x** - Core Logic
* **Tkinter** - Graphical User Interface
* **Matplotlib** - Data Visualization

## 📦 How to Run

1.  Clone the repository:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/memory-hierarchy-simulator.git](https://github.com/YOUR_USERNAME/memory-hierarchy-simulator.git)
    ```
2.  Install dependencies:
    ```bash
    pip install matplotlib
    ```
3.  Run the application:
    ```bash
    python main.py
    ```
## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
