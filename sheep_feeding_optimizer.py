import pulp

# Define the model
model = pulp.LpProblem("Sheep_Nutrition_Optimization", pulp.LpMinimize)

# Nutritional requirements for flushing stage
protein_req = 9.19  # % Protein required
tdn_req = 59.46  # % TDN required
dmi_req = 4.0  # Dry Matter Intake (lbs/day)

# Forage characteristics
P_f = 5  # Forage Protein (%)
T_f = 34  # Forage TDN (%)
DM_f = 90  # Dry Matter Content of Forage (%)

# Dry matter availability per acre (lbs)
D_f = 2000  # lbs/acre available forage
S = 90  # Stocking rate (sheep per acre)

# Correctly compute maximum forage intake per sheep (dry matter basis)
max_forage_intake = min(dmi_req, (D_f * DM_f / 100) / S)

# Add forage intake as a decision variable
forage_intake = pulp.LpVariable("forage_intake", lowBound=0, upBound=max_forage_intake)

# Define supplemental feeds with their properties
feeds = {
    "Purina_Accuration": {"cost": 129.99 / 200, "protein": 25, "tdn": 75, "dm": 90, "min_intake": 0.5, "max_intake": 1.0},
    "Corn": {"cost": 0.15, "protein": 9, "tdn": 90, "dm": 88, "min_intake": 0, "max_intake": 3.0},
    "Soybean_Meal": {"cost": 0.30, "protein": 44, "tdn": 80, "dm": 89, "min_intake": 0, "max_intake": 2.0},
}

# Define decision variables (amount of each feed consumed per day per sheep)
x = {f: pulp.LpVariable(f"x_{f}", lowBound=feeds[f]["min_intake"], upBound=feeds[f]["max_intake"])
     for f in feeds}

# Objective function: Minimize total cost of supplementation
model += pulp.lpSum(feeds[f]["cost"] * x[f] for f in feeds), "Total_Cost"

# Calculate forage contributions based on the variable forage intake
forage_protein = forage_intake * P_f / 100
forage_tdn = forage_intake * T_f / 100
forage_dm = forage_intake

# Constraints: Ensure nutritional needs are met
model += pulp.lpSum(feeds[f]["protein"] * x[f] for f in feeds) + forage_protein >= protein_req, "Protein_Requirement"
model += pulp.lpSum(feeds[f]["tdn"] * x[f] for f in feeds) + forage_tdn >= tdn_req, "TDN_Requirement"

# Dry Matter Intake Constraint
model += pulp.lpSum((feeds[f]["dm"] / 100) * x[f] for f in feeds) + forage_dm <= dmi_req, "DMI_Limit"

# Add explicit solver to fix NoneType error
solver = pulp.PULP_CBC_CMD()
model.solve(solver)

# Display results
print(f"Status: {pulp.LpStatus[model.status]}")
if model.status == pulp.LpStatusOptimal:
    # Daily intake per sheep
    print("\nOptimal Feed Plan (Flushing Stage):")
    print(f"  Forage intake: {forage_intake.value():.2f} lbs/day")
    for f in feeds:
        print(f"  {f}: {x[f].value():.2f} lbs/day")
    
    # Total feed consumption
    total_supplement = sum(x[f].value() for f in feeds)
    total_feed = forage_intake.value() + total_supplement
    print(f"\nTotal feed consumption: {total_feed:.2f} lbs/sheep/day")
    print(f"DMI requirement: {dmi_req:.2f} lbs/sheep/day")
    
    # Actual nutrition provided
    actual_protein = forage_intake.value() * P_f/100 + sum(x[f].value() * feeds[f]["protein"]/100 for f in feeds)
    actual_tdn = forage_intake.value() * T_f/100 + sum(x[f].value() * feeds[f]["tdn"]/100 for f in feeds)
    
    print(f"\nNutritional Analysis:")
    print(f"  Protein: {actual_protein:.2f} lbs ({actual_protein/total_feed*100:.2f}%)")
    print(f"  Required protein: {protein_req/100*dmi_req:.2f} lbs ({protein_req:.2f}%)")
    print(f"  TDN: {actual_tdn:.2f} lbs ({actual_tdn/total_feed*100:.2f}%)")
    print(f"  Required TDN: {tdn_req/100*dmi_req:.2f} lbs ({tdn_req:.2f}%)")
    
    # Calculate pasture duration
    daily_forage_all_sheep = forage_intake.value() * S  # lbs/day for all sheep
    total_available_forage = D_f * DM_f/100  # lbs of DM available on the entire pasture
    days_on_pasture = total_available_forage / daily_forage_all_sheep if daily_forage_all_sheep > 0 else float('inf')
    
    print(f"\nPasture Duration Analysis:")
    print(f"  Sheep per acre: {S}")
    print(f"  Total forage available: {total_available_forage:.2f} lbs DM")
    print(f"  Daily forage consumption (all sheep): {daily_forage_all_sheep:.2f} lbs DM/day")
    print(f"  Days pasture will last: {days_on_pasture:.1f} days")
    
    print(f"\nTotal Cost: ${pulp.value(model.objective):.2f} per sheep per day")
else:
    print("The model is infeasible. Here's what might be wrong:")
    print("1. Your protein and TDN requirements may be comparing % to lbs")
    print("2. Fix by changing constraints to:")
    print("   model += pulp.lpSum(x[f] * feeds[f]['protein']/100 for f in feeds) + forage_protein >= (protein_req/100) * dmi_req")
    print("   model += pulp.lpSum(x[f] * feeds[f]['tdn']/100 for f in feeds) + forage_tdn >= (tdn_req/100) * dmi_req")
