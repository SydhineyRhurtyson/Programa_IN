# # from scipy.optimize import linprog

# # c = [8, 6, 10, 9]

# # A_ub = [[1, 1, 0, 0],
# #         [0, 0, 1, 1],
# #         [-1, 0, -1, 0],  # Correção: Multiplicado por -1 (demanda >= 90)
# #         [0, -1, 0, -1]]  # Correção: Multiplicado por -1 (demanda >= 110)

# # b_ub = [120, 100, -90, -110] # Correção: Lado direito multiplicado por -1

# # res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None)]*4, method="highs")
# # print(res.x, res.fun)
# import pulp
# fab, cli = ["F1", "F2"], ["C1", "C2"]
# cap = {"F1": 120, "F2": 100}
# dem = {"C1": 90, "C2": 110}
# custo = {("F1","C1"): 8, ("F1","C2"): 6,("F2","C1"): 10,("F2","C2"): 9}

# prob = pulp.LpProblem("Transporte", pulp.LpMinimize)
# x = pulp.LpVariable.dicts("x", custo, lowBound=0)
# prob += pulp.lpSum(custo[k] * x[k] for k in custo)
# for f in fab:
#         prob += pulp.lpSum(x[f, c] for c in cli) <= cap[f]
# for c in cli:
#         prob += pulp.lpSum(x[f, c] for f in fab) >= dem[c]
# prob.solve()
# print("Status:", pulp.LpStatus[prob.status])
# if pulp.LpStatus[prob.status] == "Optimal":
#         for v in prob.variables():
#                 print(v.name, "=", v.varValue)
#         print(pulp.value(prob.objective))
