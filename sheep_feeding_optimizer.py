import pulp

# Define the model
model = pulp.LpProblem("Sheep_Nutrition_Optimization", pulp.LpMinimize)

# Time periods (e.g., Flushing and Early Gestation)
time_periods = ["Flushing", "Early_Gestation"]

# Nutritional requirements for each stage (%)
protein_req = {"Flushing": 9.19, "Early_Gestation": 9.31}
tdn_req = {"Flushing": 59.46, "Early_Gestation": 55.17}

# Forage characteristics
P_f = 5  # Forage Protein (%)
T_f = 34  # Forage TDN (%)

# Dry matter availability per acre (lbs) and consumption fraction
D_t = {"Flushing": 2000, "Early_Gestation": 1800}  # lbs/acre
F_t = {"Flushing": 0.04, "Early_Gestation": 0.04}  # % forage consumed per sheep
S = 5  # Stocking rate (sheep per acre)

# Define supplemental feeds with their properties
feeds = {
    "Purina_Accuration": {"cost": 129.99 / 200, "protein": 25, "tdn": 75, "min_intake": 0.5, "max_intake": 1.0},
    "Corn": {"cost": 0.15, "protein": 9, "tdn": 90, "min_intake": 0, "max_intake": 3.0},
    "Soybean_Meal": {"cost": 0.30, "protein": 44, "tdn": 80, "min_intake": 0, "max_intake": 2.0},
}

# Define decision variables (amount of each feed consumed per day per sheep)
x = {(f, t): pulp.LpVariable(f"x_{f}_{t}", lowBound=feeds[f]["min_intake"], upBound=feeds[f]["max_intake"])
     for f in feeds for t in time_periods}

# Objective function: Minimize total cost of supplementation
model += pulp.lpSum(feeds[f]["cost"] * x[f, t] for f in feeds for t in time_periods), "Total_Cost"

# Constraints: Ensure nutritional needs are met for each stage
for t in time_periods:
    forage_protein = P_f * F_t[t] * (S * D_t[t]) / S  # Protein intake from forage per sheep
    forage_tdn = T_f * F_t[t] * (S * D_t[t]) / S  # TDN intake from forage per sheep

    model += pulp.lpSum(feeds[f]["protein"] * x[f, t] for f in feeds) + forage_protein >= protein_req[t], f"Protein_Req_{t}"
    model += pulp.lpSum(feeds[f]["tdn"] * x[f, t] for f in feeds) + forage_tdn >= tdn_req[t], f"TDN_Req_{t}"

# Solve the model
model.solve()

# Display results
print(f"Status: {pulp.LpStatus[model.status]}")
if model.status == pulp.LpStatusOptimal:
    print("\nOptimal Feed Plan:")
    for t in time_periods:
        for f in feeds:
            print(f"  {t} - {f}: {x[f, t].varValue:.2f} lbs/day")
    print(f"\nTotal Cost: ${pulp.value(model.objective):.2f} per sheep per day")
