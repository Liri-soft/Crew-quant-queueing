## Core Features

1. Analyzes call volumes for each hour of each day
2. Calculates exact staff numbers needed using proven call center math
3. Creates and compares different shift patterns
4. Finds the most cost-effective schedule
5. Provides detailed reports and visual charts
6. Validates staffing plans through simulation

## Detailed Code Explanation

### 1. Call Data Analysis (`erlang_staffing.py`)

This file is the foundation of the system. Here's exactly what it does:

**Call Data Structure:**
```python
arrival_rate_urgent = {
    "Monday": [4, 2, 1, 2, 2, 1, 2, 4, 8, 23, 77, 176, ...],  # 24 numbers for each hour
    "Tuesday": [4, 3, 2, 2, 2, 2, 2, 3, 12, 36, 83, ...],
    # ... data for all days
}
```
- Each number represents calls received in that hour
- Data organized by day and hour
- Allows for different patterns each day

**Staff Calculations:**
1. Takes the call volume for each hour
2. Applies the Erlang C formula:
   ```
   Traffic = (Calls per hour × Average call time) ÷ 60 minutes
   Staff needed = Calculate to handle traffic with 80% answered without wait
   Final staff = Staff needed ÷ 70% efficiency
   ```

**Key Settings:**
- Call handle time: 6.3 minutes average
- Staff efficiency: 70% (accounts for breaks, training, admin)
- Service goal: 80% of calls answered without waiting
- These can be adjusted in the code if needed

### 2. Shift Pattern Creation (`shift_optimizer.py`)

Creates and evaluates different ways to schedule staff:

**How Patterns Work:**
```
Pattern 0: [00:00-08:00] [08:00-16:00] [16:00-24:00]
Pattern 1: [01:00-09:00] [09:00-17:00] [17:00-01:00]
Pattern 2: [02:00-10:00] [10:00-18:00] [18:00-02:00]
... and so on
```

**Pattern Evaluation Process:**
1. For each pattern:
   - Looks at each shift's hours
   - Finds the busiest hour in that shift
   - Sets staff number based on busiest hour
   - Calculates total staff and hours needed

2. Compares patterns based on:
   - Total number of staff needed
   - Total working hours required
   - How well it matches call volumes

### 3. Schedule Optimization (`ideal_shift.py`)

Finds the most efficient schedule by:

1. **Daily Analysis:**
   - Tests each pattern against each day's call volumes
   - Calculates exact staff needs for each shift
   - Measures how busy staff will be
   - Records total costs and hours

2. **Weekly Analysis:**
   - Combines daily results
   - Finds patterns that work well all week
   - Balances consistency with efficiency

3. **Output Generation:**
   ```
   Pattern 3 Results:
   - Morning (03:00-11:00): 18 staff
   - Day (11:00-19:00): 85 staff
   - Night (19:00-03:00): 26 staff
   Total: 129 staff
   Efficiency: 60.5%
   ```

### 4. Report Generation (`create_excel_report.py`)

Creates a comprehensive Excel workbook with:

1. **Staffing Needs Tab:**
   - Hour-by-hour staff requirements
   - Color-coded busy periods
   - Daily totals and averages

2. **Shift Patterns Tab:**
   - All possible patterns
   - Staff needed for each
   - Efficiency ratings

3. **Best Patterns Tab:**
   - Most efficient pattern for each day
   - Staff numbers by shift
   - Cost comparisons

### 5. Call Center Simulation (`simulation.py` and `shift_simulation.py`)

There are two different approaches to call generation in the hourly and shift simulations.

#### Hourly Simulation (`simulation.py`)
This module provides hour-by-hour validation of our Erlang C staffing calculations:

1. **Simulation Architecture and Methodology:**
   - Built on SimPy, a Python discrete-event simulation framework
   - Creates a virtual call center environment with configurable parameters
   - Implements the exact number of agents calculated for each hour
   - Generates simulated calls using actual historical call volumes
   - Models complete caller journey from arrival through queue to service/abandonment
   - Uses event-driven processing to accurately represent call center dynamics

2. **Key Parameters and Configuration Options:**
   - **Average Handle Time (AHT):** 6.3 minutes (378 seconds) as the mean, but each call varies randomly
   - **Service Level Target:** Calls answered within 20 seconds (measured as percentage)
   - **Caller Patience Model:** Exponential distribution with 2-minute average (tha patience is randomly genrated on an average 2 minutes) 
   - **Call Volume:** Based on historical data for each hour/day
   - **Call Arrival Pattern:** Random arrivals distributed across the hour
   - **Variable Service Times:** Each call's duration follows an exponential distribution with AHT as the mean

3. **Detailed Simulation Process:**
   ```python
   def run_simulation(num_agents, arrival_rate_per_hour, service_time_seconds=AHT, 
                     avg_patience_seconds=AVG_PATIENCE):
   ```
   - **Input Parameters:** Number of agents, expected call volume, average service time, and average patience time
   - **Environment Setup:** Creates a SimPy environment with the specified number of agents
   - **Call Generation Process:** 
     ```python
     def call_generator(env, agents):
         # Generates random arrival times spread throughout the hour
         arrival_times = np.sort(np.random.uniform(0, SIM_DURATION, NUM_CALLS))
     ```
   - **Call Handling Process:**
     ```python
     def handle_call(env, agents):
         # Each call has randomized service time and caller patience
         variable_service_time = np.random.exponential(service_time_seconds)
         patience = np.random.exponential(avg_patience_seconds)
     ```
   - **Results Collection:** Tracks wait times, abandonment rates, and service levels for each hour

4. **Analysis and Metrics:**
   - **Volumetric Analysis:** Compares expected vs. actual calls handled
   - **Service Level Achievement:** Percentage of calls answered within target time
   - **Abandonment Analysis:** Number and percentage of callers who hang up
   - **Wait Time Statistics:** Average and maximum times callers wait
   - **Agent Utilization:** How busy agents are throughout the hour

5. **Implementation Details:**
   - Uses `numpy.random.uniform()` to generate call arrival patterns
   - Implements exponential distribution for service times and patience
   - Uses SimPy's resource management for agent allocation
   - Employs concurrent processing to handle multiple calls simultaneously
   - Properly handles boundary conditions like zero calls or insufficient agents
   - Uses SimPy's event mechanism to model caller abandonment when patience is exceeded

#### Shift-Based Simulation (`shift_simulation.py`)
This module validates entire shift patterns with continuously varying call loads:

1. **Core Functionality and Purpose:**
   - Evaluates performance of complete shift patterns (typically 8-hour shifts)
   - Models real-world conditions where agents remain fixed while call volumes vary
   - Handles inter-hour dependencies where queues from busy periods affect later hours
   - Provides end-to-end validation of our optimized staffing plan
   - Assesses service level consistency throughout complete shifts

2. **Simulation Infrastructure:**
   ```python
   def run_shift_simulation(num_agents, hourly_arrival_rates, shift_hours=8, 
                          service_time_seconds=AHT, avg_patience_seconds=AVG_PATIENCE):

   
   ```
   - hourly_arrival_rates is an array containing call volumes for each hour in the shift.
   - **Environment:** Creates a continuous SimPy environment spanning multiple hours
   - **Agents:** Fixed number throughout the shift (as in real-world operations)
   - **Call Volumes:** Variable rates for each hour within the shift
   - **Duration:** Configurable shift length (default 8 hours)
   - **Queue Management:** Continuous queue that persists between hours

3. **Call Generation System:**
   ```python
   def call_generator(env, agents):
       # For each hour in the shift
       for hour, rate in enumerate(hourly_arrival_rates):
           # Generate arrivals for this hour
           if rate > 0:
               # Generate random arrival times within this hour
               hour_arrivals = np.random.uniform(hour*3600, (hour+1)*3600, int(rate))
   ```
   - **Hour-by-Hour Processing:** Iterates through each hour in the shift
   - **Variable Call Rates:** Handles different volumes for each hour
   - **Time Conversion:** Converts hour index to simulation seconds
   - **Random Distribution:** Creates realistic call arrival patterns
   - **Call Creation:** Generates call entities that flow through the system

4. **Call Processing and Queuing Logic:**
   ```python
   def handle_call(env, agents):
       # Generate variable service and patience times
       service_time = np.random.exponential(service_time_seconds)
       patience = np.random.exponential(avg_patience_seconds)
       
       # Try to get an agent
       with agents.request() as req:
           results = yield env.timeout(patience) | req
   ```
   - results = yield env.timeout(patience) | req line is implementing a race condition between getting an agent and running out of patience.
   - **Service Time Modeling:** Realistic variation in how long calls take
   - **Patience Modeling:** Different thresholds for when callers abandon
   - **Resource Contention:** Accurate representation of queue formation
   - **Abandonment Logic:** Callers leave if their patience is exceeded
   - **Wait Time Tracking:** Records how long each caller waits

5. **Comprehensive Analysis Framework:**
   - **Shift-Level Metrics:** Performance for each complete shift
   - **Day-Level Aggregation:** Combines shifts to show daily performance
   - **Weekly Assessment:** Provides complete picture across all days
   - **Service Level Calculation:** Percentage of calls meeting target wait time
   - **Abandonment Analysis:** Patterns of when and why callers give up

6. **Example Results and Interpretation:**
   ```
   First Shift (03:00-11:00): 
   - 28 calls arrived
   - 28 calls handled successfully
   - 0 calls abandoned
   - Average wait time: 1.2 seconds
   - Service level: 97.5% answered within target time
   - This shift had 12 agents working
   ```
   This output demonstrates how the shift performed: all calls were handled with excellent service levels.

7. **Validation Methodology:**
   - Tests each day with the optimized pattern determined by `ideal_shift.py`
   - Measures performance against service level targets
   - Identifies potential problem periods where service might suffer
   - Confirms consistent performance across all days
   - Provides confidence that the staffing plan will work in practice



## How to Use

1. **Setup:**
   ```powershell
   # Install all required packages using requirements.txt
   pip install -r requirements.txt

2. **Prepare Your Data:**
   - Open `erlang_staffing.py`
   - Update the `arrival_rate_urgent` dictionary with your call volumes
   - Adjust settings if needed (handle time, efficiency, etc.)

3. **Run the Program:**
   ```powershell
   python main.py
   ```

4. **Review Results:**
   - Check `hourly_staffing_needs.png` for visual patterns
   - Open `StaffingReport.xlsx` for detailed analysis
   - Look at terminal output for quick insights

## Output Examples

1. **Visual Output (`hourly_staffing_needs.png`):**
   - Line graph showing staff needs
   - Different color for each day
   - Easy to spot patterns and peaks

2. **Excel Report (`StaffingReport.xlsx`):**
   - Complete analysis of all options
   - Best patterns highlighted
   - Efficiency calculations included




