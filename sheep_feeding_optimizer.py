import pulp

# Define the model
model = pulp.LpProblem("Sheep_Nutrition_Optimization", pulp.LpMinimize)

# Nutritional requirements for flushing stage
protein_requirement_pct = 9.19  # Protein requirement (%)
tdn_requirement_pct = 59.46  # TDN requirement (%)
daily_dmi_limit = 4.0  # Maximum Dry Matter Intake (lbs/day)

# Forage characteristics
forage_protein_pct = 5  # Forage Protein (%)
forage_tdn_pct = 34  # Forage TDN (%)
forage_dm_pct = 90  # Dry Matter Content of Forage (%)

# Dry matter availability per acre (lbs)
available_forage_per_acre = 2000  # lbs/acre available forage
sheep_per_acre = 90  # Stocking rate (sheep per acre)

# Correctly compute maximum forage intake per sheep (dry matter basis)
max_forage_per_sheep = min(daily_dmi_limit, (available_forage_per_acre * forage_dm_pct / 100) / sheep_per_acre)

# Add forage intake as a decision variable
forage_intake = pulp.LpVariable("forage_intake", lowBound=0, upBound=max_forage_per_sheep)

# Define supplemental feeds with their properties
supplements = {
    "Purina_Accuration": {"cost": 129.99 / 200, "protein": 25, "tdn": 75, "dm": 90, "min_intake": 0, "max_intake": 1.0},
    "Corn": {"cost": 0.15, "protein": 9, "tdn": 90, "dm": 88, "min_intake": 0, "max_intake": 3.0},
    "Soybean_Meal": {"cost": 0.30, "protein": 44, "tdn": 80, "dm": 89, "min_intake": 0, "max_intake": 2.0},
}

# Define decision variables (amount of each feed consumed per day per sheep)
supplement_intake = {feed: pulp.LpVariable(f"intake_{feed}", lowBound=supplements[feed]["min_intake"], 
                                         upBound=supplements[feed]["max_intake"])
                   for feed in supplements}

# Objective function: Minimize total cost of supplementation
model += pulp.lpSum(supplements[feed]["cost"] * supplement_intake[feed] for feed in supplements), "Total_Cost"

# Calculate forage nutrient contributions
forage_protein_lbs = forage_intake * forage_protein_pct / 100
forage_tdn_lbs = forage_intake * forage_tdn_pct / 100
forage_dm_lbs = forage_intake

# Calculate required nutrients based on exactly daily_dmi_limit pounds of feed
protein_req_lbs = (protein_requirement_pct / 100) * daily_dmi_limit
tdn_req_lbs = (tdn_requirement_pct / 100) * daily_dmi_limit

# Define a variable for total feed intake
total_feed = forage_intake + pulp.lpSum(supplement_intake[feed] for feed in supplements)

# Constraint: Ensure Total DMI equals exactly the requirement
# This makes percentage calculations work correctly
model += total_feed == daily_dmi_limit, "Exact_DMI"

# Constraints: Ensure nutritional needs are met (in pounds)
model += pulp.lpSum(supplements[feed]["protein"] / 100 * supplement_intake[feed] for feed in supplements) + forage_protein_lbs >= protein_req_lbs, "Protein_Requirement"
model += pulp.lpSum(supplements[feed]["tdn"] / 100 * supplement_intake[feed] for feed in supplements) + forage_tdn_lbs >= tdn_req_lbs, "TDN_Requirement"

# Dry Matter Content constraint (adjust for DM content of feeds)
# This is needed because not all feeds are 100% dry matter
model += pulp.lpSum((supplements[feed]["dm"] / 100) * supplement_intake[feed] for feed in supplements) + forage_dm_lbs * (forage_dm_pct / 100) <= daily_dmi_limit, "DMI_Limit"

# Add explicit solver to fix NoneType error
solver = pulp.PULP_CBC_CMD()
model.solve(solver)

# Display results
print(f"Status: {pulp.LpStatus[model.status]}")
if model.status == pulp.LpStatusOptimal:
    # Daily intake per sheep
    print("\nOptimal Feed Plan (Flushing Stage):")
    print(f"  Forage intake: {forage_intake.value():.2f} lbs/day")
    for feed in supplements:
        print(f"  {feed}: {supplement_intake[feed].value():.2f} lbs/day")
    
    # Total feed consumption
    total_supplement = sum(supplement_intake[feed].value() for feed in supplements)
    total_feed = forage_intake.value() + total_supplement
    print(f"\nTotal feed consumption: {total_feed:.2f} lbs/sheep/day")
    print(f"DMI requirement: {daily_dmi_limit:.2f} lbs/sheep/day")
    
    # Actual nutrition provided
    actual_protein = forage_intake.value() * forage_protein_pct/100 + sum(supplement_intake[feed].value() * supplements[feed]["protein"]/100 for feed in supplements)
    actual_tdn = forage_intake.value() * forage_tdn_pct/100 + sum(supplement_intake[feed].value() * supplements[feed]["tdn"]/100 for feed in supplements)
    
    print(f"\nNutritional Analysis:")
    print(f"  Protein: {actual_protein:.2f} lbs ({actual_protein/total_feed*100:.2f}%)")
    print(f"  Required protein: {protein_requirement_pct/100*daily_dmi_limit:.2f} lbs ({protein_requirement_pct:.2f}%)")
    print(f"  TDN: {actual_tdn:.2f} lbs ({actual_tdn/total_feed*100:.2f}%)")
    print(f"  Required TDN: {tdn_requirement_pct/100*daily_dmi_limit:.2f} lbs ({tdn_requirement_pct:.2f}%)")
    
    # Calculate pasture duration
    daily_forage_all_sheep = forage_intake.value() * sheep_per_acre  # lbs/day for all sheep
    total_available_forage = available_forage_per_acre * forage_dm_pct/100  # lbs of DM available on the entire pasture
    days_on_pasture = total_available_forage / daily_forage_all_sheep if daily_forage_all_sheep > 0 else float('inf')
    
    print(f"\nPasture Duration Analysis:")
    print(f"  Sheep per acre: {sheep_per_acre}")
    print(f"  Total forage available: {total_available_forage:.2f} lbs DM")
    print(f"  Daily forage consumption (all sheep): {daily_forage_all_sheep:.2f} lbs DM/day")
    print(f"  Days pasture will last: {days_on_pasture:.1f} days")
    
    # Cost analysis
    daily_cost_per_sheep = pulp.value(model.objective)
    daily_cost_all_sheep = daily_cost_per_sheep * sheep_per_acre
    total_grazing_cost = daily_cost_all_sheep * days_on_pasture
    
    print(f"\nFeed Cost Analysis:")
    print(f"  Feed Cost per sheep per day: ${daily_cost_per_sheep:.2f}")
    print(f"  Feed Cost for all {sheep_per_acre} sheep per day: ${daily_cost_all_sheep:.2f}")
    print(f"  Total feed costs for {days_on_pasture:.1f} days of grazing: ${total_grazing_cost:.2f}")
else:
    print("The model is infeasible. Here's what might be wrong:")
    print("1. Your protein and TDN requirements may be comparing % to lbs")
    print("2. Fix by changing constraints to:")
    print("   model += pulp.lpSum(supplement_intake[feed] * supplements[feed]['protein']/100 for feed in supplements) + forage_protein_lbs >= (protein_requirement_pct/100) * daily_dmi_limit")
    print("   model += pulp.lpSum(supplement_intake[feed] * supplements[feed]['tdn']/100 for feed in supplements) + forage_tdn_lbs >= (tdn_requirement_pct/100) * daily_dmi_limit")
