import pulp

# Define the model
model = pulp.LpProblem("Sheep_Nutrition_Optimization", pulp.LpMinimize)

# Nutritional requirements for different stages (only for sheep weighing 154 lbs)
sheep_nutrition_data = {
    "Maintenance_Single": {"weeks": 16, "dm_intake": 2.6, "tdn": 1.5, "protein": 0.25, "tdn_pct": 57.69, "protein_pct": 9.62},
    "Maintenance_Twin": {"weeks": 14, "dm_intake": 2.6, "tdn": 1.5, "protein": 0.25, "tdn_pct": 57.69, "protein_pct": 9.62},
    "Flushing": {"weeks": 5, "dm_intake": 4.0, "tdn": 2.3, "protein": 0.36, "tdn_pct": 57.50, "protein_pct": 9.00},
    "Nonlactating": {"weeks": 15, "dm_intake": 3.1, "tdn": 1.7, "protein": 0.29, "tdn_pct": 54.84, "protein_pct": 9.35},
    "Last_4_Weeks_Gestation": {"weeks": 4, "dm_intake": 4.0, "tdn": 2.3, "protein": 0.42, "tdn_pct": 57.50, "protein_pct": 10.50},
    "First_6_Weeks_Lactation_Single": {"weeks": 8, "dm_intake": 5.5, "tdn": 3.6, "protein": 0.73, "tdn_pct": 65.45, "protein_pct": 13.27},
    "First_6_Weeks_Lactation_Twin": {"weeks": 8, "dm_intake": 6.2, "tdn": 4.0, "protein": 0.92, "tdn_pct": 64.52, "protein_pct": 14.84},
}

# Hardcoded flushing stage
current_nutrition_stage = "Last_4_Weeks_Gestation"

# Set nutritional requirements based on the hardcoded stage
nutrition = sheep_nutrition_data[current_nutrition_stage]
protein_requirement_pct = nutrition["protein_pct"]
tdn_requirement_pct = nutrition["tdn_pct"]
daily_dmi_limit = nutrition["dm_intake"]

print(f"Using {current_nutrition_stage} stage for sheep weighing 154 lbs:")
print(f"  DM Intake: {daily_dmi_limit} lbs/day")
print(f"  TDN Requirement: {tdn_requirement_pct}%")
print(f"  Protein Requirement: {protein_requirement_pct}%")

# Forage characteristics by maturity stage
forage_quality = {
    "Early_vegetative": {"protein": 18, "fiber": 24, "tdn": 60, "dm": 25},  # High moisture (75% water)
    "Late_vegetative": {"protein": 15, "fiber": 25, "tdn": 58, "dm": 30}, 
    "Early_flowering": {"protein": 15, "fiber": 26, "tdn": 56, "dm": 35},
    "Late_flowering": {"protein": 10, "fiber": 29, "tdn": 50, "dm": 45},
    "Mature": {"protein": 6, "fiber": 33, "tdn": 40, "dm": 75},
    "Dry": {"protein": 5, "fiber": 34, "tdn": 34, "dm": 90},   
    "Dry_leached": {"protein": 3, "fiber": 35, "tdn": 30, "dm": 92}
}

# Hardcoded forage stage
current_forage_stage = "Dry" 

# Set forage characteristics based on selected stage
forage = forage_quality[current_forage_stage]
forage_protein_pct = forage["protein"]
forage_tdn_pct = forage["tdn"]
forage_dm_pct = forage["dm"]  

print(f"Using forage at {current_forage_stage} stage: {forage_protein_pct}% protein, {forage_tdn_pct}% TDN, {forage_dm_pct}% DM")

# Dry matter availability per acre (lbs)
available_forage_per_acre = 2000  # lbs/acre available forage
sheep_per_acre = 90  # Stocking rate (sheep per acre)

# Correctly compute maximum forage intake per sheep (dry matter basis)
max_forage_per_sheep = min(daily_dmi_limit, (available_forage_per_acre * forage_dm_pct / 100) / sheep_per_acre)
min_forage_per_sheep = daily_dmi_limit * 0.5 if daily_dmi_limit * 0.5 <= max_forage_per_sheep else max_forage_per_sheep  # Minimum forage intake (75% of max)

# Add forage intake as a decision variable
forage_intake = pulp.LpVariable("forage_intake", lowBound=min_forage_per_sheep, upBound=max_forage_per_sheep)

# Calculate max intake for Purina Accuration Range Pellet based on 1/3 protein rule
total_protein_required_lbs = (protein_requirement_pct/100) * daily_dmi_limit  # 9.19% of 4.0 lbs
max_protein_from_supplement_lbs = total_protein_required_lbs / 3  # 1/3 of total protein
range_pellet_protein_pct = 33  # protein percentage in the supplement
max_range_pellet_intake = max_protein_from_supplement_lbs / (range_pellet_protein_pct/100)

# Update the supplements dictionary with calculated maximum intake
supplements = {
    # Feed mill supplements
    "Corn": {"cost": 0.25, "protein": 9, "tdn": 90, "dm": 88, "min_intake": 0, "max_intake": 3.0, "is_block": False},
    "Soybean_Meal": {"cost": 0.30, "protein": 44, "tdn": 80, "dm": 89, "min_intake": 0, "max_intake": 2.0, "is_block": False},
    "Wheat_Middlings": {"cost": 0.13, "protein": 16, "tdn": 77, "dm": 89, "min_intake": 0, "max_intake": 2.5, "is_block": False},
    "Molasses": {"cost": 0.20, "protein": 4, "tdn": 75, "dm": 75, "min_intake": 0.05, "max_intake": 0.5, "is_block": False},
    "Limestone": {"cost": 0.05, "protein": 0, "tdn": 0, "dm": 99, "min_intake": 0, "max_intake": 0.1, "is_block": False},
    
    # Feed store supplements
    "Purina_Accuration": {"cost": 129.99 / 200, "protein": 25, "tdn": 85, "dm": 90, "min_intake": 0, "max_intake": 1.0, "is_block": True},
    "Cascade_Pellets": {"cost": 11.49 / 50, "protein": 14.5, "tdn": 68, "dm": 90, "min_intake": 0, "max_intake": 2.0, "is_block": False},
    "Purina_Stocker_Grower": {"cost": 17.99 / 50, "protein": 14, "tdn": 68, "dm": 90, "min_intake": 0, "max_intake": 2.0, "is_block": False},
    "Accuration_Block_Concord": {"cost": 129.99 / 200, "protein": 25, "tdn": 85, "dm": 96, "min_intake": 0, "max_intake": 1.0, "is_block": True},
    "Rangeland_Tub_Wilco": {"cost": 104.99 / 125, "protein": 23, "tdn": 85, "dm": 96, "min_intake": 0, "max_intake": 1.0, "is_block": True},
    "Accuration_Block_Wilco": {"cost": 149.99 / 200, "protein": 25, "tdn": 85, "dm": 96, "min_intake": 0, "max_intake": 1.0, "is_block": True},
    "Rangeland_Allstock_Tub": {"cost": 99.99 / 125, "protein": 15, "tdn": 85, "dm": 96, "min_intake": 0, "max_intake": 1.0, "is_block": True},
    
    # Range pellet with dynamically calculated max intake
    "Purina_Accuration_Range_Pellet": {"cost": 14.50 / 50, "protein": 33, "tdn": 85, "dm": 90, "min_intake": 0, "max_intake": max_range_pellet_intake, "is_block": True},
}

# Define decision variables (amount of each feed consumed per day per sheep)
supplement_intake = {feed: pulp.LpVariable(f"intake_{feed}", lowBound=supplements[feed]["min_intake"], 
                                         upBound=supplements[feed]["max_intake"])
                   for feed in supplements}

# Create binary variables for protein blocks (1 if used, 0 if not)
block_used = {feed: pulp.LpVariable(f"use_{feed}", cat='Binary') 
             for feed in supplements if supplements[feed]["is_block"]}

# Link block usage to intake (if block_used=0, then intake must be 0)
for feed in block_used:
    model += supplement_intake[feed] <= supplements[feed]["max_intake"] * block_used[feed], f"Link_{feed}"

# Add constraint: At most one protein block can be used
model += pulp.lpSum(block_used[feed] for feed in block_used) <= 1, "One_Block_Only"

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
    print(f"\nOptimal Feed Plan ({current_nutrition_stage} Stage, Forage: {current_forage_stage}):")
    print(f"  Forage intake: {forage_intake.value():.2f} lbs/day")
    for feed in supplements:
        print(f"  {feed}: {supplement_intake[feed].value():.2f} lbs/day")
    
    # Total feed consumption
    total_supplement = sum(supplement_intake[feed].value() for feed in supplements)
    total_feed = forage_intake.value() + total_supplement
    print(f"\nTotal feed consumption: {total_feed:.2f} lbs/sheep/day")
    print(f"Total supplement: {total_supplement:.2f} lbs/sheep/day")
    print(f"DMI requirement: {daily_dmi_limit:.2f} lbs/sheep/day")
    
    # Actual nutrition provided
    actual_protein = forage_intake.value() * forage_protein_pct/100 + sum(supplement_intake[feed].value() * supplements[feed]["protein"]/100 for feed in supplements)
    actual_tdn = forage_intake.value() * forage_tdn_pct/100 + sum(supplement_intake[feed].value() * supplements[feed]["tdn"]/100 for feed in supplements)
    
    print(f"\nNutritional Analysis ({current_nutrition_stage} Stage):")
    print(f"  Protein: {actual_protein:.2f} lbs ({actual_protein/total_feed*100:.2f}%)")
    print(f"  Required protein: {protein_requirement_pct/100*daily_dmi_limit:.2f} lbs ({protein_requirement_pct:.2f}%)")
    print(f"  TDN: {actual_tdn:.2f} lbs ({actual_tdn/total_feed*100:.2f}%)")
    print(f"  Required TDN: {tdn_requirement_pct/100*daily_dmi_limit:.2f} lbs ({tdn_requirement_pct:.2f}%)")
    
    # Calculate pasture duration
    daily_forage_all_sheep = forage_intake.value() * sheep_per_acre  # lbs/day for all sheep
    total_available_forage = available_forage_per_acre * forage_dm_pct/100  # lbs of DM available on the entire pasture
    days_on_pasture = total_available_forage / daily_forage_all_sheep if daily_forage_all_sheep > 0 else float('inf')
    
    # Calculate supplemental feed quantities
    daily_supplement_all_sheep = total_supplement * sheep_per_acre
    total_supplement_needed = daily_supplement_all_sheep * days_on_pasture
    
    print(f"\nSupplemental Feed Requirements ({current_forage_stage} Forage):")
    print(f"  Daily supplement per sheep: {total_supplement:.2f} lbs/day")
    print(f"  Daily supplement for all {sheep_per_acre} sheep: {daily_supplement_all_sheep:.2f} lbs/day")
    print(f"  Total supplement needed for {days_on_pasture:.1f} days: {total_supplement_needed:.2f} lbs")
    
    # Print detailed supplement requirements
    print("\nDetailed Supplement Requirements:")
    for feed in supplements:
        if supplement_intake[feed].value() > 0.001:  # Only show feeds that are actually used
            daily_amount = supplement_intake[feed].value() * sheep_per_acre
            total_amount = daily_amount * days_on_pasture
            feed_cost = supplements[feed]["cost"] * total_amount
            print(f"  {feed}: {daily_amount:.2f} lbs/day, {total_amount:.2f} lbs total (${feed_cost:.2f})")
    
    print(f"\nPasture Duration Analysis ({current_forage_stage} Forage):")
    print(f"  Sheep per acre: {sheep_per_acre}")
    print(f"  Total forage available: {total_available_forage:.2f} lbs DM")
    print(f"  Daily forage consumption (all sheep): {daily_forage_all_sheep:.2f} lbs DM/day")
    print(f"  Days pasture will last: {days_on_pasture:.1f} days")
    
    # Cost analysis
    daily_cost_per_sheep = pulp.value(model.objective)
    daily_cost_all_sheep = daily_cost_per_sheep * sheep_per_acre
    total_grazing_cost = daily_cost_all_sheep * days_on_pasture
    
    print(f"\nFeed Cost Analysis ({current_nutrition_stage} Stage, Forage: {current_forage_stage}):")
    print(f"  Feed Cost per sheep per day: ${daily_cost_per_sheep:.2f}")
    print(f"  Feed Cost for all {sheep_per_acre} sheep per day: ${daily_cost_all_sheep:.2f}")
    print(f"  Total feed costs for {days_on_pasture:.1f} days of grazing: ${total_grazing_cost:.2f}")
else:
    print("The model is infeasible. Please check your constraints and inputs.")

