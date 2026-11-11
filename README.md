# 🎒 Problema da Mochila: Clássico vs Quântico (Qiskit)

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Qiskit-1.x-purple.svg)](https://qiskit.org/)

Este repositório explora a resolução do famoso **Problema da Mochila (Knapsack Problem)**, um desafio clássico de otimização combinatória, comparando duas abordagens distintas: a Programação Dinâmica (Computação Clássica) e o algoritmo QAOA (Computação Quântica).

## 📖 Sobre o Projeto

O objetivo deste projeto é demonstrar como problemas de otimização clássicos podem ser mapeados e resolvidos em computadores quânticos utilizando a biblioteca **Qiskit** da IBM. 

O código aborda os seguintes conceitos:
- **Programação Dinâmica:** Algoritmo clássico exato que avalia subproblemas iterativamente.
- **Modelagem Matemática (QUBO):** Conversão de funções e restrições de desigualdade em Otimização Binária Irrestrita Quadrática.
- **QAOA (Quantum Approximate Optimization Algorithm):** Algoritmo híbrido clássico-quântico rodando em um simulador local (`StatevectorSampler`) otimizado pelo método `COBYLA`.

## 🛠️ Tecnologias Utilizadas

- **Python**
- **Qiskit** (Framework quântico)
- **Qiskit Optimization** (Mapeamento de restrições para QUBO)
- **Qiskit Algorithms** (Implementação do QAOA)
- **SciPy** (Otimizadores clássicos sob o capô)

## 🚀 Como Executar

### 1. Instalação dos Pré-requisitos

Certifique-se de ter o **[Python 3.x](https://www.python.org/downloads/)** instalado em sua máquina. 

**Você não precisa instalar as bibliotecas manualmente!** 🤖
O projeto foi desenvolvido com um script inteligente de auto-instalação. Ao rodar o programa pela primeira vez, ele verificará o seu ambiente local e usará o próprio terminal, de forma invisível, para baixar e instalar automaticamente todas as bibliotecas necessárias (como `qiskit`, `qiskit-optimization` e `scipy`). 

> **Nota:** Certifique-se de estar conectado à internet durante a primeira execução para que o Python consiga realizar os downloads com sucesso.