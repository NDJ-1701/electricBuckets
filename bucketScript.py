from itertools import product as it_product
import numpy as np
import time

# "CONSTANTS" TO AVOID MAKING MISTAKES IN PANEL DESIGN
AN = 0 # PHASE A TO NEUTRAL
CN = 1
PA = 0 # PHASE A, LINE TO LINE
PB = 1
PC = 2
NOMOTOR = 0
MOTOR = 1
LN = 0
LL = 1
P3 = 2

prev_best = 10**5
biA = 99999
biB = 99999
biC = 99999
bL2N = 99999
bL3N = 99999

variable_setup = []
static_setup = []
active_panel = None
result_maximum = 99999
attempts = 0
possibilities = 0

# ANSI Escape codes
RESET = "\033[0m"
COLORS = {
    'red': "\033[1;31m",
    'green': "\033[32m",
    'yellow': "\033[33m",
    'blue': "\033[34m",
    'magenta': "\033[35m",
    'cyan': "\033[36m",
    'white': "\033[37m"
}

# Helper function to print comma-separated strings with color last, and optional end
def print_colored(*args, end="\n"):
    # The last argument is the color
    color = args[-1]
    # The rest are the strings to print
    text = " ".join(map(str, args[:-1]))

    # Get the color code, default to white if not found
    color_code = COLORS.get(color, COLORS['white'])

    # Print the colored text with the given end parameter
    print(f"{color_code}{text}{RESET}", end=end)

def print_progress_bar(current, total, bar_length=60):
    """
    Prints a new progress bar each time the function is called.

    Args:
        current (int): The current progress value.
        total (int): The final value when the progress is complete.
        bar_length (int): The length of the progress bar in characters (default is 40).
    """
    # Calculate progress percentage
    progress = 1 if total == 0 else current / total
    filled_length = int(bar_length * progress)

    # Build the bar
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    # Print the progress bar (no overwriting)
    barColor = "green" if current == total else "cyan"
    if total > 1000000:
        cur = current / 1000000
        ttl = total / 1000000
        print_colored(f"Progress: |{bar}| {int(progress * 100)}%, Combo: {cur:.2f}M/{ttl:.2f}M", barColor)
    else:
        print_colored(f"Progress: |{bar}| {int(progress * 100)}%, Combo: {current}/{total}", barColor)

class Panel:
    def __init__(self, name="Panel", limit_to_results_under=99999, variable_circuits=None, restricted_circuits=None, as_built_circuits=None):
        # Default to empty lists if no arguments are provided
        self.name = name
        self.limit_to_results_under = limit_to_results_under
        self.variable_circuits = variable_circuits if variable_circuits is not None else []
        self.restricted_circuits = restricted_circuits if restricted_circuits is not None else []
        self.as_built_circuits = as_built_circuits if as_built_circuits is not None else []
        self.subpanels = []  # Initialize subpanels as an empty list
    
    def append_from(self, other_panel):
        # Append circuits from other panel
        self.variable_circuits.extend(other_panel.variable_circuits)
        self.restricted_circuits.extend(other_panel.restricted_circuits)

    def add_subpanel(self, subpanel):
        """Add a subpanel to the list of subpanels."""
        self.subpanels.append(subpanel)
    
    def use_as_built(self):
        self.variable_circuits = []
        self.restricted_circuits = self.as_built_circuits


    def __repr__(self):
        return (f"Panel(limit_to_results_under: {self.limit_to_results_under}, "
                f"variable_circuits: {self.variable_circuits}, "
                f"restricted_circuits: {self.restricted_circuits}, "
                f"subpanels: {self.subpanels})")

def loadSetup(panel: Panel):
    global variable_setup
    global static_setup
    global active_panel
    global result_maximum
    result_maximum = panel.limit_to_results_under
    variable_setup = panel.variable_circuits
    static_setup = panel.restricted_circuits
    active_panel = panel

OFFICE = Panel(
    ########### WARNING: THIS PANEL IS QUIRKY. ALL 2 POLE ITEMS MUST BE IN LOCATION 2, THERE IS ONLY ONE OPTION
    #### THIS PANEL IS BALANCED AT 62.3A, BUT IT PUTS ALL THE POWER ON L2/L3. IT MAY BE BENEFICIAL TO PUT POWER FROM OTHER PANELS ON L3/L1+L1/L2
    name = "office",
    limit_to_results_under = 300,
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
    # (1, "unknown load", 85, 0, 1),
    # (1, "left of cage lights", 100, 0, 1),
    # (7, "various receptacles", 150, 0, 1),
    # (1, "fire panel", 180, 0, 1),
    # (1, "front bathroom receptacle", 200, 0, 1),
    # (1, "front bathroom light and fan and entryway", 250, 0, 1),
    # (3, "various lights and receptacles", 250, 0, 1),
    # (1, "stairway and office lights", 262, 0, 1),
    # (1, "patio light", 280, 0, 1),
    # (1, "dry room side lighting", 280, 0, 1),
    # (3, "var receptacles", 360, 0, 1),
    # (1, "entry light", 490, 0, 1),
    # (1, "dry and hall light", 495, 0, 1),
    # (1, "inner office receptacles", 500, 0, 1),

    #(1, "AC", 1170, 1, 2),
    #(1, "mini split", 1935, 1, 2),
    #(1, "HP", 1700, 1, 2),
    #(2, "Dehu + air handler", 1830, 1, 2)
    ],
    # RESTRICTED CIRCUITS
    restricted_circuits = [
    (1, "unknown load", 85, 0, 1, 0),
    (1, "left of cage lights", 100, 0, 1, 0),

    (1, "network receptacles north", 150, 0, 1, 1),
    (1, "network recept", 150, 0, 1, 0),

    (1, "dry room recep1", 150, 0, 1, 1),
    (1, "dry room recep2", 150, 0, 1, 0),
    (1, "dry room recep3", 150, 0, 1, 0),
    (1, "dry room recep4", 150, 0, 1, 1),
    (1, "dry room recep5", 150, 0, 1, 0),
    

    (1, "fire panel", 180, 0, 1, 0),
    (1, "front bathroom receptacle", 200, 0, 1, 0),
    (1, "top bathroom light", 250, 0, 1, 0),
    (1, "front bathroom light and fan and entryway", 250, 0, 1, 1),
    
    (1, "office receptacles and exit sign", 250, 0, 1, 1),
    (1, "entry receptacles", 250, 0, 1, 1),

    (1, "stairway and office lights", 262, 0, 1, 0),
    (1, "patio light", 280, 0, 1, 0),
    (1, "dry room side lighting", 280, 0, 1, 1),
    (1, "recept cage", 360, 0, 1, 0),
    (1, "recept main office", 360, 0, 1, 0),
    (1, "shop sink recept", 360, 0, 1, 1),
    (1, "entry light", 490, 0, 1, 0),
    (1, "dry and hall light", 495, 0, 1, 1),
    (1, "inner office receptacles", 500, 0, 1, 1),

    (1, "AC", 1170, 1, 2, 2), # all 2 pole items must be L2-L3 on a 2 pole panel.
    (1, "mini split", 1935, 1, 2, 2),
    (1, "HP", 1700, 1, 2, 2), 
    (1, "Dehu + air handler", 1830, 1, 2, 2),
    (1, "Dehu + air handler", 1830, 1, 2, 2)
    ]
)

OFFICE_AC = Panel(
    name = "OfficeAC",
    limit_to_results_under = 300,
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
     
    ],
    # RESTRICTED CIRCUITS
    restricted_circuits = [
        # (1, "AC", 12000, 1, 3, -1), # this is the old value that is wrong
        (1, "AC", 2213.28, 1, 3, -1), # this is the 15.9 FLA, times 0.58*240
    ]
)

GARAGE = Panel(
    name = "Garage",
    limit_to_results_under = 300,
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
    # (1, "RO PUMP", 2040, 1, 2, -1), ## note this is a single phase panel, so all 2 pole breakers must be set to the C phase
    (1, "receptacles", 1620, 1, 1, -1) 
    ],
    # RESTRICTED CIRCUITS
    restricted_circuits = [
    (1, "RO PUMP", 2040, 1, 2, 2),
    #(1, "receptacles", 810, 1, 1, 0),
    #(1, "receptacles", 810, 1, 1, 1)
    ]
)

HVAC = Panel(
    name = "HVAC",
    limit_to_results_under = 300,
    # VARIABLE CIRCUITS
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
        # (4, "AC", 4530, 1, 3, -1),
        # (2, "HP", 6027, 1, 3, -1),
        # (10, "dehumidifiers", 3130, 1, 2, -1),
        # (1, "receptacle", 360, 0, 1, -1)
    ],
    # RESTRICTED CIRCUITS
    restricted_circuits = [
        ##### this is the as-designed version:
        # (4, "AC", 4530, 1, 3, -1),
        # (2, "HP", 6027, 1, 3, -1),
        # (4, "dehumidifiers", 3130, 1, 2, 0),
        # (3, "dehumidifiers", 3130, 1, 2, 1),
        # (3, "dehumidifiers", 3130, 1, 2, 2),
        # (1, "receptacle", 360, 0, 1, 1)
        ##### this is the as-designed version with more realistic loads for the ACs:
        (3, "AC", 18955.6, 1, 3, -1),
        #(2, "AC", 18955.6*.35, 1, 3, -1), # diversity factor 0.35
        (1, "HP", 9228.4, 1, 3, -1),
        #(1, "HP", 9228.4*.35, 1, 3, -1), # diversity factor 0.35
        (4, "dehumidifiers", 3130, 1, 2, 0),
        (3, "dehumidifiers", 3130, 1, 2, 1),
        (3, "dehumidifiers", 3130, 1, 2, 2),
        (1, "receptacle", 360, 0, 1, 1)
        ##### this is the reorganized version:
        # (4, "AC", 4530, 1, 3, -1),
        # (2, "HP", 6027, 1, 3, -1),
        # (4, "dehumidifiers", 3130, 1, 2, 0),
        # (4, "dehumidifiers", 3130, 1, 2, 1),
        # (2, "dehumidifiers", 3130, 1, 2, 2),
        # (1, "receptacle", 360, 0, 1, 1)
    ]
)

F1 = Panel(
    name = "flower 1",
    limit_to_results_under = 999, # best is 156.3362
    # VARIABLE CIRCUITS
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
        # (10, "Rack Lights", 5040, 0, 2, -1),
        # (5, "Rack Receptacles", 2160, 0, 1, -1),
        # (1, "co2 controller", 180, 0, 1, -1),
        # (1, "general lighting", 280, 0, 1, -1),
        # (1, "general receptacles", 360, 0, 1, -1),
        # (1, "sump pump", 600, 1, 1, -1),
        # (1, "co2 purge fan", 1284, 1, 2, -1),
    ],
    # RESTRICTED CIRCUITS
    # 157.4183 : solution I chose RL(4, 0, 0)  RL(0, 4, 0)  RL(0, 0, 2)  RR(3, 0)  RR(0, 2)  CC(0, 1)  GL(0, 1)  GR(0, 1)  SP(0, 1)  CPF(0, 1, 0)  
    restricted_circuits = [
    # AS-BUILT:
        (4, "Rack Lights", 5040, 0, 2, PA),
        (2, "Rack Lights", 5040, 0, 2, PB),
        (4, "Rack Lights", 5040, 0, 2, PC),
        (2, "Rack Receptacles", 2160, 0, 1, AN),
        (3, "Rack Receptacles", 2160, 0, 1, CN),
        (1, "co2 controller", 180, 0, 1, AN),
        (1, "general lighting", 280, 0, 1, AN),
        (1, "general receptacles", 360, 0, 1, CN),
        (1, "sump pump", 600, 1, 1, CN),
        (1, "co2 purge fan", 1284, 1, 2, PB)
    ## REORGANIZED
        # (4, "Rack Lights", 5040, 0, 2, 0),
        # (4, "Rack Lights", 5040, 0, 2, 1),
        # (2, "Rack Lights", 5040, 0, 2, 2),
        # (3, "Rack Receptacles", 2160, 0, 1, 0),
        # (2, "Rack Receptacles", 2160, 0, 1, 1),
        # (1, "co2 controller", 180, 0, 1, 1),
        # (1, "general lighting", 280, 0, 1, 1),
        # (1, "general receptacles", 360, 0, 1, 1),
        # (1, "sump pump", 600, 1, 1, 1),
        # (1, "co2 purge fan", 1284, 1, 2, 1),
    ]
)

F1_NoLights = Panel(
    name = "flower 1, lights off",
    limit_to_results_under = 170, # best is 156.3362
    # VARIABLE CIRCUITS
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
        # (5, "Rack Receptacles", 2160, 0, 1, -1),
        # (1, "co2 controller", 180, 0, 1, -1),
        # (1, "general lighting", 280, 0, 1, -1),
        # (1, "general receptacles", 360, 0, 1, -1),
        # (1, "sump pump", 600, 1, 1, -1),
        # (1, "co2 purge fan", 1284, 1, 2, -1),
    ],
    # RESTRICTED CIRCUITS
    # 157.4183 : solution I chose RL(4, 0, 0)  RL(0, 4, 0)  RL(0, 0, 2)  RR(3, 0)  RR(0, 2)  CC(0, 1)  GL(0, 1)  GR(0, 1)  SP(0, 1)  CPF(0, 1, 0)  
    restricted_circuits = [
    # AS-BUILT:
        # (4, "Rack Lights", 5040, 0, 2, PA),
        # (2, "Rack Lights", 5040, 0, 2, PB),
        # (4, "Rack Lights", 5040, 0, 2, PC),
        (2, "Rack Receptacles", 2160, 0, 1, AN),
        (3, "Rack Receptacles", 2160, 0, 1, CN),
        (1, "co2 controller", 180, 0, 1, AN),
        (1, "general lighting", 280, 0, 1, AN),
        (1, "general receptacles", 360, 0, 1, CN),
        (1, "sump pump", 600, 1, 1, CN),
        (1, "co2 purge fan", 1284, 1, 2, PB)
    # reorganized
        # (3, "Rack Receptacles", 2160, 0, 1, 0),
        # (2, "Rack Receptacles", 2160, 0, 1, 1),
        # (1, "co2 controller", 180, 0, 1, 1),
        # (1, "general lighting", 280, 0, 1, 1),
        # (1, "general receptacles", 360, 0, 1, 1),
        # (1, "sump pump", 600, 1, 1, 1),
        # (1, "co2 purge fan", 1284, 1, 2, 1),
    ]
)

VEG = Panel(
    name = "veg",
    limit_to_results_under = 170,
    # VARIABLE CIRCUITS
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [
        # (8, "Rack Lights", 2520, 0, 2, -1),
        # (2, "Rack Receptacles", 2160, 0, 1, -1),

        # (2, "Quest Dehus", 2700, 1, 2, -1),
        # (1, "Excel", 6666.6667, 1, 3, -1),
        # (1, "Daikin", 3063.8298, 1, 3, -1),

        # (1, "wall receptacle", 360, 0, 1, -1),
        # (1, "door receptacle", 360, 0, 1, -1),
        # (1, "sump pump", 600, 1, 1, -1),
        # (1, "work lights", 360, 0, 1, -1),
    ],
    # RESTRICTED CIRCUITS
    # 104.523 : solution I chose RL(4, 0, 0)  RL(0, 2, 0)  RL(0, 0, 2)  RR(1, 0)  RR(0, 1)  QD(0, 2, 0)  E(1, 1, 1)  D(1, 1, 1)  WR(0, 1)  DR(0, 1)  SP(1, 0)  WL(1, 0)
    restricted_circuits = [
    # as planned
        (4, "Rack Lights", 2520, 0, 2, 0),
        (2, "Rack Lights", 2520, 0, 2, 1),
        (2, "Rack Lights", 2520, 0, 2, 2),

        (1, "Rack Receptacles", 2160, 0, 1, 0),
        (1, "Rack Receptacles", 2160, 0, 1, 0),

        (2, "Quest Dehus", 2700, 1, 2, 1),
        (1, "Excel", 6666.6667, 1, 3, -1),
        (1, "Daikin", 3063.8298, 1, 3, -1),

        (1, "wall receptacle", 360, 0, 1, 1),
        (1, "door receptacle", 360, 0, 1, 1),
        (1, "sump pump", 600, 1, 1, 0),
        (1, "work lights", 360, 0, 1, 0),
    # reorganized
        # (4, "Rack Lights", 2520, 0, 2, 0),
        # (2, "Rack Lights", 2520, 0, 2, 1),
        # (2, "Rack Lights", 2520, 0, 2, 2),

        # (1, "Rack Receptacles", 2160, 0, 1, 0),
        # (1, "Rack Receptacles", 2160, 0, 1, 1),

        # (2, "Quest Dehus", 2700, 1, 2, 1),
        # (1, "Excel", 6666.6667, 1, 3, -1),
        # (1, "Daikin", 3063.8298, 1, 3, -1),

        # (1, "wall receptacle", 360, 0, 1, 1),
        # (1, "door receptacle", 360, 0, 1, 1),
        # (1, "sump pump", 600, 1, 1, 0),
        # (1, "work lights", 360, 0, 1, 0),
    ]
)

TESTER = Panel(
    name = "tester",
    limit_to_results_under = 300,
    # VARIABLE CIRCUITS
    # (count, label, voltAmps, is_motor, poles, assignment)
    variable_circuits = [        
    (19, "socket", 360, 0, 1, -1),
    (1, "general lighting", 720, 0, 1, -1),
    (2, "AC", 3000, 1, 2, -1),
    (1, "Dehu", 3130, 1, 2, -1)
    ],
    # RESTRICTED CIRCUITS
    restricted_circuits = [
    (1, "socket", 360, 0, 1, 0),
    (8, "general lighting", 720, 0, 1, 0),
    (1, "AC", 3000, 0, 2, 1),
    (1, "Dehu", 3130, 0, 2, 1)
    ]
)

def print_scheme(result, combo):
    firstSet = len(variable_setup)
    for index, arrangment in enumerate(combo):
        name = None
        if index < firstSet:
            name = variable_setup[index][1]
        else:
            name = static_setup[index - firstSet][1]
        name_parts = name.split()
        initials = "".join([part[0].upper() for part in name_parts])
        print_colored(initials, "yellow", end="")
        print_colored(arrangment, " ", "yellow", end="")
    print()


def optimize(iL3N, iA, iB, iC, iL2N):
    # Define the functions for the three equations
    def calculate_iL1(A, B):
        return (A**2 + B**2 + A*B)**0.5

    def calculate_iL2(B, iC, iL2N):
        return (B**2 + (iC + iL2N)**2 + B * (iC + iL2N))**0.5

    def calculate_iL3(A, iC, iL3N):
        return (A**2 + (iC + iL3N)**2 + A * (iC + iL3N))**0.5
    
    iL1 = calculate_iL1(iA, iB)
    iL2 = calculate_iL2(iB, iC, iL2N)
    iL3 = calculate_iL3(iA, iC, iL3N)
    worst1 = max(iL1, iL2, iL3)
    # print(f"Sub-optimal values:")
    # print(f"iL3N = {iL3N}")
    # print(f"iA = {iA}")
    # print(f"iB = {iB}")
    # print(f"iC = {iC}")    
    # print(f"iL2N = {iL2N}")
    print_colored(f"Results of the equations prior to optimization:, {worst1:.3f}", "red")
    print(f"iL1 = {iL1}")
    print(f"iL2 = {iL2}")
    print(f"iL3 = {iL3}")

    # Step 1: Calculate the initial sum of iA, iB, and iC
    initial_sum_ABC = iA + iB + iC
    initial_sum_LN = iL2N + iL3N

    # Step 2: Set iL2N = iL3N = initial_sum_LN / 2 to satisfy the constraint
    iL2N = iL3N = initial_sum_LN / 2

    # Step 3: Start with iA = iB = (initial_sum_ABC / 3) as a starting point
    Y = initial_sum_ABC / 3
    iA = iB = Y
    iC = initial_sum_ABC - 2 * Y

    # Step 4: Iteratively adjust iA, iB, and iC to minimize the differences

    # Minimize the differences between iL1, iL2, and iL3
    min_difference = float('inf')
    optimal_Y = Y
    optimal_iC = iC

    # Iterate over possible values of Y to find the minimum difference
    for Y in np.linspace(0, initial_sum_ABC, 1000):
        iA = iB = Y
        iC = initial_sum_ABC - 2 * Y

        iL1 = calculate_iL1(Y, Y)
        iL2 = calculate_iL2(Y, iC, iL2N)
        iL3 = calculate_iL3(Y, iC, iL3N)

        # Calculate the maximum difference between the three values
        max_difference = max(abs(iL1 - iL2), abs(iL2 - iL3), abs(iL3 - iL1))

        if max_difference < min_difference:
            min_difference = max_difference
            optimal_Y = Y
            optimal_iC = iC

    # Step 5: Output the optimal values
    iA = iB = optimal_Y
    iC = optimal_iC
    iL1 = calculate_iL1(optimal_Y, optimal_Y)
    iL2 = calculate_iL2(optimal_Y, optimal_iC, iL2N)
    iL3 = calculate_iL3(optimal_Y, optimal_iC, iL3N)
    worst2 = max(iL1, iL2, iL3)

    # Print the results
    print(f"Optimal values:")
    print(f"iA = iB = {optimal_Y}")
    print(f"iC = {optimal_iC}")
    print(f"iL2N = iL3N = {iL2N}")
    print_colored(f"Results of the equations after optimization: {worst2:.3f}", "red")
    print(f"iL1 = {iL1}")
    print(f"iL2 = {iL2}")
    print(f"iL3 = {iL3}")
    print(f"Minimum difference between the three: {min_difference}")
    print_colored(f"Improvement over initial: {worst1 - worst2:.2f} which is a reduction of {(1-worst2/worst1)*100:.1f}%", "red")

def calculate(combo, static_combo):
    global prev_best, biA, biB, biC, biL2N, biL3N
    l3_l1 = 0
    l1_l2 = 0
    l2_l3 = 0
    l2_n = 0
    l3_n = 0

    motor_l3_l1 = 0
    motor_l1_l2 = 0
    motor_l2_l3 = 0
    motor_l2_n = 0
    motor_l3_n = 0

    combo = combo + tuple(static_combo)

    setup = variable_setup + static_setup

    for dev_num, dev_args in enumerate(setup):
        dist = combo[dev_num]
        voltAmps = dev_args[2]
        is_motor = dev_args[3]
        poles = dev_args[4]

        if poles == 1:
            l3_n += voltAmps * dist[0] # 0 is L3n, which comes first, it's on phase A
            if is_motor: motor_l3_n = max(motor_l3_n, voltAmps * 0.25 if dist[0] > 0 else 0)
            l2_n += voltAmps * dist[1] # 1 is L2n, which comes second, it's on phase C
            if is_motor: motor_l2_n = max(motor_l2_n, voltAmps * 0.25 if dist[1] > 0 else 0)
        elif poles == 2:
            l3_l1 += voltAmps * dist[0]
            if is_motor: motor_l3_l1 = max(motor_l3_l1, voltAmps * 0.25 if dist[0] > 0 else 0)
            l1_l2 += voltAmps * dist[1]
            if is_motor: motor_l1_l2 = max(motor_l1_l2, voltAmps * 0.25 if dist[1] > 0 else 0)
            l2_l3 += voltAmps * dist[2]
            if is_motor: motor_l2_l3 = max(motor_l2_l3, voltAmps * 0.25 if dist[2] > 0 else 0)
        elif poles == 3:
            split_amps = voltAmps / 3
            l3_l1 += split_amps * dist[0]
            if is_motor: motor_l3_l1 = max(motor_l3_l1, split_amps * 0.25 if dist[0] > 0 else 0)
            l1_l2 += split_amps * dist[1]
            if is_motor: motor_l1_l2 = max(motor_l1_l2, split_amps * 0.25 if dist[1] > 0 else 0)
            l2_l3 += split_amps * dist[2]
            if is_motor: motor_l2_l3 = max(motor_l2_l3, split_amps * 0.25 if dist[2] > 0 else 0)

    # keep the largest motor on phases A and C, whether those are on L-N or L-N locations
    motor_l3_l1, motor_l3_n = (0, motor_l3_n) if motor_l3_l1 < motor_l3_n else (motor_l3_l1, 0)
    motor_l2_l3, motor_l2_n = (0, motor_l2_n) if motor_l2_l3 < motor_l2_n else (motor_l2_l3, 0)

    total_va = l3_l1 + l1_l2 + l2_l3 + l2_n + l3_n
    Ava = l3_l1 + motor_l3_l1
    Bva = l1_l2 + motor_l1_l2
    Cva = l2_l3 + motor_l2_l3
    L2Nva = l2_n + motor_l2_n
    L3Nva = l3_n + motor_l3_n
    total_va_LML = Ava + Bva + Cva + L2Nva + L3Nva
    iA = Ava / 240
    iB = Bva / 240
    iC = Cva / 240
    iL2N = L2Nva / 120
    iL3N = L3Nva / 120
    iL1 = ( iA**2 + iB**2 + (iA*iB) )**0.5
    iL2 = ( iB**2 + (iC+iL2N)**2 + iB*(iC+iL2N) )**0.5
    iL3 = ( iA**2 + (iC+iL3N)**2 + iA*(iC+iL3N) )**0.5

    result = max((iL1,iL2,iL3))
    values = {"iL1": iL1, "iL2": iL2, "iL3": iL3}

    if result < prev_best:
        prev_best = result
        if result <= result_maximum or attempts == 0:
            biA = iA
            biB = iB
            biC = iC
            biL2N = iL2N
            biL3N = iL3N
            print_scheme(result, combo)
            print(f"       subtotal: L3N({l3_n}) A({l3_l1}) B({l1_l2}) C({l2_l3}) L2N({l2_n})")
            print(f"motor penalties: L3N({motor_l3_n}) A({motor_l3_l1}) B({motor_l1_l2}) C({motor_l2_l3}) L2N({motor_l2_n})")
            print(f" total with LML: L3N({L3Nva}) A({Ava}) B({Bva}) C({Cva}) L2N({L2Nva})")
            print(f"           Amps: L3N({iL3N}) A({iA}) B({iB}) C({iC}) L2N({iL2N})")
            print("   Panel Rating: ", end="")
            color = "white"
            if values["iL1"] == result: color = "red"
            else: color = "white"
            print_colored(f"{iL1:.4f} [iL1] ", color, end="")
            if values["iL2"] == result: color = "red" 
            else: color = "white"
            print_colored(f"{iL2:.4f} [iL2] ", color, end="")
            if values["iL3"] == result: color = "red"
            else: color = "white"
            print_colored(f"{iL3:.4f} [iL3] ", color, end="")
            print(f"| Total VA: ", total_va, "| Total VA + LML: ", total_va_LML)
            print_progress_bar(attempts + 1, possibilities)
            print()
    
    return (result, combo)

def display_room_menu():
    """
    Displays a menu of available rooms and handles user selection.
    Returns the selected setup or mainPanel.
    """
    # Define available rooms
    rooms = {
        1: ("OFFICE", OFFICE),
        2: ("OFFICE_AC", OFFICE_AC),
        3: ("HVAC", HVAC),
        4: ("F1", F1),
        5: ("F1_NoLights", F1_NoLights),
        6: ("VEG", VEG),
        7: ("GARAGE", GARAGE),
        8: ("All Rooms", "ALL")
    }
    
    while True:
        # Display menu
        print("\nAvailable Rooms:")
        print("-" * 20)
        for number, (name, _) in rooms.items():
            print(f"{number}. {name}")
        print("-" * 20)
        
        try:
            choice = int(input("\nEnter the number of your selection (1-8): "))
            
            if choice not in rooms:
                print("Invalid selection. Please choose a number between 1 and 8.")
                continue
                
            if choice == 8:  # All rooms selected
                mainPanel = Panel()
                # Add all individual rooms to mainPanel
                for _, (_, setup) in rooms.items():
                    if setup != "ALL":  # Skip the "All Rooms" option
                        mainPanel.append_from(setup)
                return mainPanel
            else:
                return rooms[choice][1]  # Return the selected setup
                
        except ValueError:
            print("Please enter a valid number.")

def main():
    print()
    global attempts
    global possibilities

    # setups available: OFFICE, OFFICE_AC, HVAC, F1, VEG, GARAGE, TEST

    # loadSetup(TESTER)
    # loadSetup(OFFICE)
    # loadSetup(OFFICE_AC)
    # loadSetup(HVAC)
    # loadSetup(F1)
    # loadSetup(F1_NoLights)
    # loadSetup(VEG)
    # loadSetup(GARAGE)

    # mainPanel = Panel()
    # mainPanel.append_from(OFFICE)
    # mainPanel.append_from(OFFICE_AC)
    # mainPanel.append_from(HVAC)
    # mainPanel.append_from(F1)
    # mainPanel.append_from(F1_NoLights)
    # mainPanel.append_from(VEG)
    # mainPanel.append_from(GARAGE)
    selected_setup = display_room_menu()
    loadSetup(selected_setup)

    static_combo = []
    for device_args in static_setup:
        count = device_args[0]
        poles = device_args[4]
        position = device_args[5]
        if poles == 1:
            static_combo.append( (count if position == 0 else 0, count if position == 1 else 0) )
        elif poles == 2:
            static_combo.append( (count if position == 0 else 0, count if position == 1 else 0, count if position == 2 else 0) )
        elif poles == 3:
            static_combo.append( (count, count, count) )

    all_distributions = []
    for device_args in variable_setup:
        count = device_args[0]
        poles = device_args[4]
        if poles == 1:
            all_distributions.append( [(i, count - i) for i in range(count + 1)] )
        elif poles == 2:
            all_distributions.append( [(i, j, count - i - j) for i in range(count + 1) for j in range(count - i + 1)] )
        elif poles == 3:
            all_distributions.append( [(count, count, count)] )

    all_combinations = it_product(*all_distributions)
    
    possibilities = 1
    for item in all_distributions:
        setLength = len(item)
        possibilities *= setLength # possibilities must start out equal to 1
    
    print_colored(possibilities, " combinations will be tested.", "magenta")
    time.sleep(1)

    #start_index = 0

    for combo in all_combinations:
    #for index, combo in enumerate(all_combinations[2:], start=start_index):
        (result, new_combo) = calculate(combo, static_combo)
        # if result < prev_best: ########## moved this code into calculate so I could print more stuff
        #     prev_best = result
        #     print(result, new_combo)
        attempts += 1
        if attempts % 100000 == 0:
                print_progress_bar(attempts, possibilities)
    optimize(biL3N, biA, biB, biC, biL2N)
    print_progress_bar(attempts, possibilities)

if __name__ == "__main__":
    main()  # Call the main function if the script is being run directly