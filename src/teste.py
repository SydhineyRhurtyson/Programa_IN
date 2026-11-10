from logsfacilitator import measure_time_and_memory, measure_memory
from  qiskit import QuantumCircuit


@measure_time_and_memory(folder="Data")
def print_bit(n):
    print(bin(n))

@measure_time_and_memory(folder="data")
def print_qubit(n):
    circuito = QuantumCircuit(n)
    for i in range(0,n):
        circuito.h(i)

    print(circuito.draw())

print_bit(3)
print_qubit(3)