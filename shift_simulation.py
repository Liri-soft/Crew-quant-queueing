import simpy
import numpy as np
from erlang_staffing import arrival_rate_urgent, DAYS_OF_WEEK, URGENT_TASK_WORK_MINUTES

# Convert minutes to seconds for simulation
AHT = URGENT_TASK_WORK_MINUTES * 60  # Average handling time in seconds
SHIFT_DURATION = 8 * 3600  # 8 hours in seconds
TARGET_SLA = 20  # Target answer time in seconds for service level
AVG_PATIENCE = 120  # Average caller patience in seconds (2 minutes)

def run_shift_simulation(num_agents, hourly_arrival_rates, shift_hours=8, 
                       service_time_seconds=AHT, avg_patience_seconds=AVG_PATIENCE):
    """
    Run a simulation for an entire shift (multiple hours)
    
    Parameters:
    num_agents (int): Number of agents staffed for this shift
    hourly_arrival_rates (list): List of arrival rates for each hour in the shift
    shift_hours (int): Duration of the shift in hours
    service_time_seconds (float): Average service time in seconds
    avg_patience_seconds (float): Average patience time in seconds
    
    Returns:
    dict: Simulation results
    """
    if sum(hourly_arrival_rates) == 0:
        return {
            "calls_arrived": 0,
            "calls_handled": 0,
            "calls_abandoned": 0,
            "calls_expected": 0,
            "avg_wait": 0,
            "max_wait": 0,
            "service_level": 100,
        }
    
    # Setup simulation environment
    env = simpy.Environment()
    agents = simpy.Resource(env, capacity=num_agents)
    
    # Tracking variables
    wait_times = []
    calls_handled = 0
    calls_arrived = 0
    calls_abandoned = 0
    
    # Calculate total simulation duration
    sim_duration = shift_hours * 3600  # in seconds
    
    def call_generator(env, agents):
        """Generate calls based on arrival rates that vary by hour"""
        nonlocal calls_arrived
        
        # For each hour in the shift
        for hour, rate in enumerate(hourly_arrival_rates):
            # Generate arrivals for this hour
            if rate > 0:
                # Generate random arrival times within this hour
                hour_arrivals = np.random.uniform(hour*3600, (hour+1)*3600, int(rate))
                for arrival_time in sorted(hour_arrivals):
                    # Wait until arrival time
                    yield env.timeout(arrival_time - env.now)
                    
                    # Generate a new call
                    calls_arrived += 1
                    env.process(handle_call(env, agents))

    def handle_call(env, agents):
        """Handle an incoming call with potential abandonment"""
        nonlocal calls_handled, calls_abandoned
        arrival_time = env.now
        
        # Generate variable service and patience times
        service_time = np.random.exponential(service_time_seconds)
        patience = np.random.exponential(avg_patience_seconds)
        
        # Try to get an agent
        with agents.request() as req:
            results = yield env.timeout(patience) | req
            wait_time = env.now - arrival_time
            
            # Check if call was abandoned
            if req not in results:
                calls_abandoned += 1
                return
            
            # Call was handled
            wait_times.append(wait_time)
            calls_handled += 1
            
            # Handle the call
            yield env.timeout(service_time)
    
    # Start the call generator process
    env.process(call_generator(env, agents))
    
    # Run the simulation
    env.run(until=sim_duration)
    
    # Analyze results
    if len(wait_times) > 0:
        wait_array = np.array(wait_times)
        avg_wait = np.mean(wait_array)
        max_wait = np.max(wait_array)
        service_level = np.mean(wait_array <= TARGET_SLA) * 100
    else:
        avg_wait = 0
        max_wait = 0
        service_level = 100
    
    return {
        "calls_arrived": calls_arrived,
        "calls_handled": calls_handled,
        "calls_abandoned": calls_abandoned,
        "calls_expected": sum(hourly_arrival_rates),
        "avg_wait": avg_wait,
        "max_wait": max_wait,
        "service_level": service_level,
    }

def simulate_ideal_pattern(ideal_pattern):
    """
    Simulate the performance of the ideal shift pattern
    
    Parameters:
    ideal_pattern (dict): The ideal pattern structure from find_ideal_shift_pattern()
    
    Returns:
    dict: Simulation results by day and shift
    """
    results = {}
    
    print("\n=== SIMULATING IDEAL SHIFT PATTERN PERFORMANCE ===")
    
    for day_stat in ideal_pattern['daily_stats']:
        day = day_stat['day']
        day_results = []
        
        print(f"\nSimulating {day} with Pattern {ideal_pattern['pattern_number']}:")
        
        for i, shift in enumerate(day_stat['shifts']):
            shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
            shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
            
            # Get the hours covered by this shift
            hours = shift['hours']
            
            # Get the arrival rates for these hours
            arrival_rates = [arrival_rate_urgent[day][hour] for hour in hours]
            
            # Get the number of agents for this shift
            num_agents = shift['agents_needed']
            
            # Run the simulation for this shift
            result = run_shift_simulation(num_agents, arrival_rates)
            
            # Store the results
            shift_result = {
                "shift_type": shift_type,
                "hours": hours,
                "start_time": f"{shift['start_hour']:02d}:00",
                "end_time": f"{shift['end_hour']:02d}:00",
                "agents": num_agents,
                **result
            }
            day_results.append(shift_result)
            
            # Print the results
            print(f"  {shift_type} Shift ({shift_result['start_time']}-{shift_result['end_time']}): "
                  f"{result['calls_arrived']} calls, "
                  f"{result['calls_handled']} handled, "
                  f"{result['calls_abandoned']} abandoned, "
                  f"{result['avg_wait']:.1f}s avg wait, "
                  f"{result['service_level']:.1f}% service level with {num_agents} agents")
        
        # Store the results for this day
        results[day] = day_results
        
        # Calculate day summary
        day_calls = sum(r["calls_arrived"] for r in day_results)
        day_handled = sum(r["calls_handled"] for r in day_results)
        day_abandoned = sum(r["calls_abandoned"] for r in day_results)
        day_sl = np.mean([r["service_level"] for r in day_results if r["calls_handled"] > 0])
        
        print(f"\n{day} Summary: {day_calls} calls, "
              f"{day_handled} handled, "
              f"{day_abandoned} abandoned, "
              f"{day_sl:.1f}% service level")
    
    # Calculate weekly summary
    all_shifts = [shift for day_shifts in results.values() for shift in day_shifts]
    weekly_calls = sum(shift["calls_arrived"] for shift in all_shifts)
    weekly_handled = sum(shift["calls_handled"] for shift in all_shifts)
    weekly_abandoned = sum(shift["calls_abandoned"] for shift in all_shifts)
    weekly_sl = np.mean([shift["service_level"] for shift in all_shifts if shift["calls_handled"] > 0])
    
    print(f"\nWeekly Summary: {weekly_calls} calls, "
          f"{weekly_handled} handled, "
          f"{weekly_abandoned} abandoned, "
          f"{weekly_sl:.1f}% service level")
    
    return results