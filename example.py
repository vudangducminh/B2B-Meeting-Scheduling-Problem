import sys
import signal
from pysat.pb import *
from pysat.formula import CNF, WCNF
from pysat.solvers import Glucose3
from pysat.card import CardEnc, EncType
from pysat.examples.rc2 import RC2
from math import inf
import signal
import subprocess
import time

out = sys.stdout
sys.stdin = open('input.txt', 'r')
sys.stdout = open('output.txt', 'w')

sat_solver = Glucose3()
cnf = CNF()
wcnf = WCNF()
variable_size = 0
def read_input():
    with open('input.txt', 'r') as f:
        lines = f.readlines()
    
    # Read the initial variables
    nBusiness = int(lines[0].split('=')[1].strip().rstrip(';'))
    nMeetings = int(lines[1].split('=')[1].strip().rstrip(';'))
    nTables = int(lines[2].split('=')[1].strip().rstrip(';'))
    nTotalSlots = int(lines[3].split('=')[1].strip().rstrip(';'))
    nMorningSlots = int(lines[4].split('=')[1].strip().rstrip(';'))
    
    # Parse the requested array
    requested = [[0, 0, 0]]
    i = 6  # Start after the blank line
    while i < len(lines):
        line = lines[i].strip()
        if line == '|];':
            i += 1
            break
        elif 'requested' in line and '[|' in line:
            # Handle the header line with data
            content = line.split('[|', 1)[1].rstrip(',')
            parts = content.split(',')
            if len(parts) >= 3:
                requested.append([int(parts[0].strip()), 
                                int(parts[1].strip()), 
                                int(parts[2].strip())])
        elif line.startswith('|'):
            # Remove '|' and trailing comma
            parts = line.lstrip('|').rstrip(',').split(',')
            if len(parts) >= 3:
                requested.append([int(parts[0].strip()), 
                                int(parts[1].strip()), 
                                int(parts[2].strip())])
        i += 1
    
    # Parse meetingsxBusiness if needed
    meetingsxBusiness = [[]]
    while i < len(lines):
        line = lines[i].strip()
        # Skip empty lines
        if not line:
            i += 1
            continue
        # Skip the header line "meetingsxBusiness = [" and extract first set if present
        if 'meetingsxBusiness' in line and '[' in line:
            # Extract everything after the '['
            content = line.split('[', 1)[1]
            if content.startswith('{') and ',' in content:
                # First set is on the same line
                first_set = content.lstrip('{').rstrip(',}')
                numbers = [int(x.strip()) - 1 for x in first_set.split(',') if x.strip()]
                numbers = numbers[1:]
                meetingsxBusiness.append(numbers)
        elif line.startswith('{'):
            # Regular set line
            should_break = False
            if line.endswith('},'):
                numbers_str = line.strip('{},')
            elif line.endswith('};') or line.endswith('}];'):
                numbers_str = line.strip('{};]')
                should_break = True
            else:
                i += 1
                continue
            numbers = [int(x.strip()) - 1 for x in numbers_str.split(',') if x.strip()]
            numbers = numbers[1:]
            meetingsxBusiness.append(numbers)
            if should_break:
                i += 1
                break
        elif line == '];' or line == '};':
            i += 1
            break
        i += 1
    
    # Parse nMeetingsBusiness
    nMeetingsBusiness = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if 'nMeetingsBusiness' in line and '[' in line:
            # Extract the array content
            content = line.split('[', 1)[1].rstrip('];')
            nMeetingsBusiness = [0] + [int(x.strip()) for x in content.split(',') if x.strip()]
            i += 1
            break
        i += 1
    
    # Parse forbidden (array of sets)
    forbidden = [[]]
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if 'forbidden' in line and '[' in line:
            # Extract first set if on same line
            content = line.split('[', 1)[1]
            if content.startswith('{'):
                first_set = content.lstrip('{').rstrip(',}')
                numbers = [int(x.strip()) for x in first_set.split(',') if x.strip()]
                numbers = numbers[1:]  
                forbidden.append(numbers)
        elif line.startswith('{'):
            should_break = False
            if line.endswith('},'):
                numbers_str = line.strip('{},') 
            elif line.endswith('};') or line.endswith('}];'):
                numbers_str = line.strip('{};]')
                should_break = True
            else:
                i += 1
                continue
            numbers = [int(x.strip()) for x in numbers_str.split(',') if x.strip()]
            numbers = numbers[1:]  
            forbidden.append(numbers)
            if should_break:
                i += 1
                break
        elif line == '];' or line == '};':
            i += 1
            break
        i += 1
    
    # Parse fixed (simple array of integers)
    fixed = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if 'fixed' in line and '[' in line:
            # Extract the array content
            content = line.split('[', 1)[1].rstrip('];')
            fixed = [0] + [int(x.strip()) for x in content.split(',') if x.strip()]
            i += 1
            break
        i += 1
    
    # Parse precedences (array of sets)
    precedences = [[]]
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if 'precedences' in line and '[' in line:
            # Extract first set if on same line
            content = line.split('[', 1)[1]
            if content.startswith('{'):
                first_set = content.lstrip('{').rstrip(',}')
                if first_set:  # Not empty
                    numbers = [int(x.strip()) for x in first_set.split(',') if x.strip()]
                    precedences.append(numbers)
                else:
                    precedences.append([])
        elif line.startswith('{'):
            should_break = False
            if line.endswith('},'):
                numbers_str = line.strip('{},') 
            elif line.endswith('};') or line.endswith('}];'):
                numbers_str = line.strip('{};]')
                should_break = True
            else:
                i += 1
                continue
            if numbers_str:  # Not empty
                numbers = [int(x.strip()) for x in numbers_str.split(',') if x.strip()]
                precedences.append(numbers)
            else:
                precedences.append([])
            if should_break:
                i += 1
                break
        elif line == '];' or line == '};':
            i += 1
            break
        i += 1
    
    return nBusiness, nMeetings, nTables, nTotalSlots, nMorningSlots, requested, meetingsxBusiness, nMeetingsBusiness, forbidden, fixed, precedences

# Usage
start_time = time.time()
print(f"Starting execution at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}", file=out)

nBusiness, nMeetings, nTables, nTotalSlots, nMorningSlots, requested, meetingsxBusiness, nMeetingsBusiness, forbidden, fixed, precedences = read_input()
input_time = time.time()
print(f"Input parsing completed in {input_time - start_time:.4f} seconds", file=out)

def print_solution(n):

    sat_solver.append_formula(cnf)
    print(f"Number of vars: {sat_solver.nof_vars()}")
    print(f"Number of clauses: {sat_solver.nof_clauses()}")

    sat_status = sat_solver.solve()

    if sat_status is False:
        print("No solutions found")
    else:
        solution = sat_solver.get_model()
        if solution is None:
            print("Time out")
        else:
            print(f"Solution found: {solution}")
            for i, val in enumerate(solution, start=1):
                if i <= n:
                    print(f"X{i} = {int(val > 0)}") 

read_input()

print(nBusiness, nMeetings, nTables, nTotalSlots, nMorningSlots)
print("Requested:", requested)
print("MeetingsxBusiness:", meetingsxBusiness)
print("nMeetingsBusiness:", nMeetingsBusiness)
print("Forbidden:", forbidden)
print("Fixed:", fixed)
print("Precedences:", precedences)

# x[m][t] = 1 if meeting m is scheduled at time slot t, 0 otherwise
x = [[0 for _ in range(nTotalSlots + 1)] for _ in range(nMeetings + 1)]

# Assign variable numbers to x[m][t]
for m in range(1, nMeetings + 1):
    for t in range(1, nTotalSlots + 1):
        if x[m][t] == 0:
            x[m][t] = variable_size + 1
            variable_size += 1


# Each meeting happened exactly once
for m in range(1, nMeetings + 1):
    lits = [x[m][t] for t in range(1, nTotalSlots + 1)]
    clauses = CardEnc.equals(lits=lits, bound=1, encoding=EncType.seqcounter, top_id=variable_size)
    cnf.extend(clauses)
    variable_size = max(variable_size, clauses.nv)

# No more than nTables meetings at the same time
for t in range(1, nTotalSlots + 1):
    lits = [x[m][t] for m in range(1, nMeetings + 1)]
    clauses = CardEnc.atmost(lits=lits, bound=nTables, encoding=EncType.seqcounter, top_id=variable_size)
    cnf.extend(clauses)
    variable_size = max(variable_size, clauses.nv)

# At most one meeting at moment t for the same business
for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots + 1):
        lits = [x[m][t] for m in meetingsxBusiness[p]]
        clauses = CardEnc.atmost(lits=lits, bound=1, encoding=EncType.seqcounter, top_id=variable_size)
        cnf.extend(clauses)
        variable_size = max(variable_size, clauses.nv)

# Handle time session
for m in range(1, nMeetings + 1):
    if requested[m][2] == 3: # No time restriction
        continue
    elif requested[m][2] == 1: # Morning
        for t in range(nMorningSlots + 1, nTotalSlots + 1):
            cnf.append([-x[m][t]])
    else: # Afternoon
        for t in range(1, nMorningSlots + 1):
            cnf.append([-x[m][t]])  

# y[p][t] = 1 if business p has a meeting at time slot t, 0 otherwise
y = [[0 for _ in range(nTotalSlots + 1)] for _ in range(nBusiness + 1)]

# z[p][t] = 1 if there is at least one meeting from time slot 1 to t for business p, 0 otherwise
z = [[0 for _ in range(nTotalSlots + 1)] for _ in range(nBusiness + 1)]

# h[p][t] = 1 if business p's break gets interrupted at time slot t, 0 otherwise
h = [[0 for _ in range(nTotalSlots + 1)] for _ in range(nBusiness + 1)]

for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots + 1):
        y[p][t] = variable_size + 1
        variable_size += 1 
print(y)
for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots + 1):
        z[p][t] = variable_size + 1
        variable_size += 1
        
for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots + 1):
        h[p][t] = variable_size + 1
        variable_size += 1

# Business p has nMeetingsBusiness[p] meetings
for p in range(1, nBusiness + 1):
    lits = [y[p][t] for t in range(1, nTotalSlots + 1)]
    # print(f"Business {p} has {nMeetingsBusiness[p]} meetings, lits: {lits}")
    clauses = CardEnc.equals(lits=lits, bound=nMeetingsBusiness[p], encoding=EncType.seqcounter, top_id=variable_size)
    cnf.extend(clauses)
    variable_size = max(variable_size, clauses.nv)

# Debug
# print_solution(variable_size)

# x[m][t] <= y[p][t]
for p in range(1, nBusiness + 1):
    for m in meetingsxBusiness[p]:
        for t in range(1, nTotalSlots + 1):
            cnf.append([-x[m][t], y[p][t]])

# y[p][t] <= z[p][t]
for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots + 1):
        cnf.append([-y[p][t], z[p][t]])

# z[p][t-1] <= z[p][t]
for p in range(1, nBusiness + 1):
    for t in range(2, nTotalSlots + 1):
        cnf.append([-z[p][t-1], z[p][t]])

# y[p][t+1] + not h[p][t] + z[p][t] + not y[p][t] <= 3
for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots):
        cnf.append([-y[p][t+1], h[p][t], -z[p][t], y[p][t]])

# sum(h[p][t]) <= upper_bound for each business p, where upper_bound is the maximum number of allowed break interruptions

# upper_bound = nTotalSlots # Adjust this value later
# fairness = 2 # Adjust this value later
# for p in range(1, nBusiness + 1):
#     lits = [h[p][t] for t in range(1, nTotalSlots + 1)]
#     clauses = CardEnc.atmost(lits=lits, bound=upper_bound, encoding=EncType.seqcounter, top_id=variable_size)
#     cnf.extend(clauses)
#     variable_size = max(variable_size, clauses.nv)

# lower_bound = upper_bound - fairness
# # sum(h[p][t]) >= lower_bound for each business p
# for p in range(1, nBusiness + 1):
#     lits = [h[p][t] for t in range(1, nTotalSlots + 1)]
#     clauses = CardEnc.atleast(lits=lits, bound=lower_bound, encoding=EncType.seqcounter, top_id=variable_size)
#     cnf.extend(clauses)
#     variable_size = max(variable_size, clauses.nv)

# The objective function: minimize sum(h[p][t]) for all p and t
# So the hard constraints are implemented as above, and the soft constraint is maximizing the sum of not h[p][t], which is equivalent to minimizing the sum of h[p][t].
# => MaxSAT

# Handle forbidden time slots
for p in range(1, nBusiness + 1):
    for t in forbidden[p]:
        cnf.append([-y[p][t]])  # Business p cannot have a meeting at time slot t

# Handle fixed meetings
for m in range(1, nMeetings + 1):
    if fixed[m] != 0:
        t = fixed[m]
        cnf.append([x[m][t]])  # Meeting m must be scheduled at time slot t

# Handle precedence constraints
for m in range(1, nMeetings + 1):
    for prec in precedences[m]:
        # Add staircase constraints (meeting prec must be scheduled before meeting m)
        sfx = [0 for _ in range(nTotalSlots + 1)]
        sfx[nTotalSlots] = x[prec][nTotalSlots]
        for t in range(nTotalSlots - 1, 0, -1):
            sfx[t] = variable_size + 1
            variable_size += 1
            cnf.append([-x[prec][t], sfx[t]])  # x[prec][t] => sfx[t]
            cnf.append([-sfx[t + 1], sfx[t]])  # sfx[t + 1] => sfx[t]
            cnf.append([x[prec][t], sfx[t + 1], -sfx[t]])  # not x[prec][t] and not sfx[t + 1] => not sfx[t]
        # x[m][t] + sfx[t + 1] <= 1
        for t in range(1, nTotalSlots):
            cnf.append([-x[m][t], -sfx[t + 1]])

# Add hard clauses 
for clause in cnf.clauses:
    wcnf.append(clause)  # Default weight is top (hard)

# Add soft clauses
for p in range(1, nBusiness + 1):
    for t in range(1, nTotalSlots + 1):
        wcnf.append([-h[p][t]], weight=1)

constraint_time = time.time()
print(f"Constraint building completed in {constraint_time - input_time:.4f} seconds", file=out)

def solve_maxsat():
    """
    Solve MaxSAT using pysat's built-in RC2 solver.
    Returns the model (variable assignment) if found, None otherwise.
    """
    # Create RC2 solver with the WCNF formula
    solver = RC2(wcnf)
    
    # Compute the optimal solution
    model = solver.compute()
    
    # Get the cost (number of unsatisfied soft clauses)
    if model:
        cost = solver.cost
        print(f"MaxSAT solution found with cost: {cost}", file=out)
    
    return model

# Write the WCNF to a file
wcnf.to_file('maxHS.wcnf')

# Solve
solve_start = time.time()
assignment = solve_maxsat()
solve_time = time.time()
print(f"MaxSAT solving completed in {solve_time - solve_start:.4f} seconds", file=out)

print(assignment)
# Output the schedule based on the assignment
if assignment:
    for m in range(1, nMeetings + 1):
        for t in range(1, nTotalSlots + 1):
            if x[m][t] in assignment:
                print(f"Meeting {m} → Time slot {t}")

end_time = time.time()
total_time = end_time - start_time
print(f"\n{'='*60}", file=out)
print(f"TOTAL RUNTIME: {total_time:.4f} seconds ({total_time:.2f}s)", file=out)
print(f"{'='*60}", file=out)