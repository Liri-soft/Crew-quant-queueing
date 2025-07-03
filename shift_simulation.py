import simpy
import numpy as np
from erlang_staffing import arrival_rate_urgent
from config import TARGET_SLA, DESIRED_SLA, SHIFT_HOURS, AVG_PATIENCE, LUNCH_BREAK_TIME, MAX_PERCENTAGE_AGENTS_ON_BREAK, AVG_HANDLING_TIME, CALL_COMPLEXITY_DISTRIBUTION, ACW_MIN, ACW_MAX, AGENT_EFFICIENCY

# Convert minutes to seconds for simulation
AHT = AVG_HANDLING_TIME * 60  # Average handling time in seconds
LUNCH_BREAK_DURATION = LUNCH_BREAK_TIME * 60  # Break time in seconds (break time varies for each agent)
MAX_AGENTS_ON_BREAK = MAX_PERCENTAGE_AGENTS_ON_BREAK / 100  # Convert percentage to fraction


def run_shift_simulation(num_agents, hourly_arrival_rates, shift_hours=SHIFT_HOURS,
                         service_time_seconds=AHT, avg_patience_seconds=AVG_PATIENCE, debug=False):
    """Run a simulation for an entire shift (multiple hours)"""
    # Set a fixed seed
    np.random.seed(42)

    def debug_print(message):
       """Print debug messages with current simulation time"""
       if debug:
           time_str = f"{env.now/3600:.2f}h" if env.now > 0 else "0h"
           print(f"[TIME {time_str}] {message}")

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
    
    # avilable_agents = num_agents * 0.5
    # Setup simulation environment
    env = simpy.Environment()

    agents = simpy.Resource(env, capacity=num_agents * AGENT_EFFICIENCY / 100)  # Adjust capacity based on agent efficiency
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
                hour_arrivals = np.random.uniform(hour*3600, (hour+1)*3600, rate)

                for arrival_time in sorted(hour_arrivals):
                    # Wait until arrival time
                    yield env.timeout(arrival_time - env.now) 

                    # Generate a new call
                    calls_arrived += 1
                    call_id = calls_arrived  # Unique ID for this call
                    debug_print(f"CALL {call_id} ARRIVED")
                    call_process = env.process(handle_call(env, agents, call_id))
                    # print(f"call process {call_process}")

    def handle_call(env, agents, call_id):
        """Handle an incoming call with potential abandonment"""
        nonlocal calls_handled, calls_abandoned
        arrival_time = env.now

        # Determine call complexity (normal, semicomplex, or complex)
        call_complexity = np.random.choice(['normal', 'semicomplex', 'complex'], # selecting call complexity
                                          p=CALL_COMPLEXITY_DISTRIBUTION["probabilities"]) # probabilities of selecting call complexity
                                          

        # Set handling time based on complexity
        if call_complexity == 'normal':
            # Normal calls are shorter
            complexity_factor = 1.0
        elif call_complexity == 'semicomplex':
            # Semicomplex calls use the standard time
            complexity_factor = CALL_COMPLEXITY_DISTRIBUTION["complexity_factors"]["semicomplex"]  # increased times the average handling time
        else:  # complex
            # Complex calls take longer
            complexity_factor = CALL_COMPLEXITY_DISTRIBUTION["complexity_factors"]["complex"]  # increased times the average handling time

        # Generate variable service and patience times
        service_time = np.random.exponential(service_time_seconds * complexity_factor)
        # gentate after call work time (After call is complited agent need some time to document the call)
        acw = np.random.uniform(ACW_MIN, ACW_MAX) # seconds after call work time
        # print(f"service time {service_time}")
        patience = np.random.exponential(avg_patience_seconds)
    
        
        # Try to get an agent
        with agents.request() as req:
            debug_print(f"CALL {call_id} REQUESTING AGENT")
            results = yield env.timeout(patience) | req # Wait for either getting an agent or running out of patience time
            wait_time = env.now - arrival_time # storing wait time
        
            # Check if call was abandoned
            if req not in results:  
                calls_abandoned += 1
                debug_print(f"CALL {call_id} ABANDONED after {wait_time:.1f}s")
                return
            
            # Call was handled
            debug_print(f"CALL {call_id} GOT AGENT after {wait_time:.1f}s wait")
            wait_times.append(wait_time)
            calls_handled += 1
        
            # Handle the call
            yield env.timeout(service_time + acw)  # Include after call work time
            debug_print(f"CALL {call_id} FINISHED ({service_time:.1f}s talk + {acw:.1f}s ACW)")
            # print(f"call no {calls_handled} service time {service_time}")

            

    def break_scheduler(env, agents):
        """Schedule breaks for agents during the shift"""

        # Calculate maximum agents that can be on break at once
        max_on_break = max(1, int(num_agents * MAX_AGENTS_ON_BREAK))

        # Number of break slots needed (based on max agents on break)
        num_break_slots = int(np.ceil(num_agents / max_on_break))

        # Calculate middle of shift
        mid_shift = (shift_hours / 2) * 3600  # Middle of shift in seconds


        # Calculate the total time span from start of first break to start of last break
        total_break_span = (num_break_slots - 1) * LUNCH_BREAK_DURATION

        # Calculate start time for first break group so all breaks are centered around mid-shift
        first_break_start = mid_shift - (total_break_span / 2)

        def agent_on_break(env, duration, break_id, group_id):
            """Process for an agent going on break"""
            # Request an agent (removing them from the available pool)
            with agents.request() as agent_req:
                yield agent_req
                debug_print(f"BREAK {break_id} (Group {group_id}) GOT AGENT")
            
            adherence_to_break = np.random.choice([1.0, 1.1, 1.2, 1.3],  # 60% chance of taking full break, 20% chance of taking 10% longer, etc.
                                         p=[0.60, 0.20, 0.10, 0.10]) # giving probabilities to choose different adherence levels
            
            actual_duration = duration * adherence_to_break
            
            debug_print(f"BREAK {break_id} (Group {group_id}) STARTED ({actual_duration:.1f}s)")
            # print(f"break started at {env.now}secs at 8 hr shift on break for {actual_duration} seconds")

            # Wait for break duration
            yield env.timeout(actual_duration)
            
            debug_print(f"BREAK {break_id} (Group {group_id}) FINISHED")
        
        # Schedule breaks for groups of agents
        agent_count = 0
        break_counter = 0

        for group in range(num_break_slots):
            # Calculate remaining agents
            remaining = num_agents - agent_count

            # Calculate group size (min of max_on_break or remaining agents)
            group_size = min(max_on_break, remaining)

            # Calculate break start time for this group
            break_start = first_break_start + (group * LUNCH_BREAK_DURATION)
            # print({break_start})

            # Wait until break time for this group
            if break_start > env.now:
                debug_print(f"WAITING {break_start - env.now:.1f}s for Break Group {group+1}")
                yield env.timeout(break_start - env.now)

            debug_print(f"SCHEDULING BREAK GROUP {group+1} ({group_size} agents)")
            # Send each agent in the group on break
            for i in range(group_size):
                 break_counter += 1
                 agent_process = env.process(agent_on_break(env, LUNCH_BREAK_DURATION, break_counter, group+1))
                # print(f"Agent {agent_process} on break")
            agent_count = agent_count + group_size

    # Start the call generator process
    env.process(call_generator(env, agents))
    env.process(break_scheduler(env, agents))
    # print(f"break process {group_break}")
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

        print(
            f"\nSimulating {day} with Pattern {ideal_pattern['pattern_number']}:")

        for i, shift in enumerate(day_stat['shifts']):
            shift_names = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"]
            shift_type = shift_names[i] if i < len(
                shift_names) else f"Shift {i+1}"

            # Get the hours covered by this shift
            hours = shift['hours']

            # Get the arrival rates for these hours
            arrival_rates = [arrival_rate_urgent[day][hour] for hour in hours]

            # Get the number of agents for this shift
            num_agents = shift['agents_needed']
            
            # Run the simulation for this shift
            result = run_shift_simulation(num_agents, arrival_rates, debug=False)

            # Store the results
            shift_result = {
                "shift_type":shift_type,
                "hours": hours,
                "start_time": f"{shift['start_hour']:02d}:00",
                "end_time": f"{shift['end_hour']:02d}:00",
                "agents": num_agents,
                "calls_arrived": result["calls_arrived"],
                "calls_handled": result["calls_handled"],
                "calls_abandoned": result["calls_abandoned"],
                "calls_expected": result["calls_expected"],
                "avg_wait": result["avg_wait"],
                "max_wait": result["max_wait"],
                "service_level": result["service_level"]
            }
            day_results.append(shift_result)

            # Print the results
            print (f"SIMULATION ON ERLANG C CALCULATION FOR {shift_type} Shift")
            print(f"  {shift_type} Shift ({shift_result['start_time']}-{shift_result['end_time']}): "
                  f"{result['calls_arrived']} calls, "
                  f"{result['calls_handled']} handled, "
                  f"{result['calls_abandoned']} abandoned/Not Answered, "
                  f"{result['avg_wait']:.1f}s avg wait, "
                  f"{result['max_wait']:.1f}s max wait, "
                  f"{result['service_level']:.1f}% service level (Ans within 20 seconds) {num_agents} agents")
            
            
            # add +1 agent to num agent until service level is above 95%
            if result['service_level'] >= DESIRED_SLA:
                print('SEMULATION ON ERLANG C CALCULATION FOR SHIFT IS ABOVE 95%')
            else:
                print('SEMULATION AFTER INCREASING AGENTS UNTIL SERVICE LEVEL IS ABOVE 95%')
            while result['service_level'] < DESIRED_SLA:
                num_agents += 1
                result = run_shift_simulation(num_agents, arrival_rates, debug=False)
                shift_result['agents'] = num_agents
                shift_result['service_level'] = result['service_level']
                shift_result['calls_arrived'] = result['calls_arrived']
                shift_result['calls_handled'] = result['calls_handled']
                shift_result['calls_abandoned'] = result['calls_abandoned']
                shift_result['avg_wait'] = result['avg_wait']
                shift_result['max_wait'] = result['max_wait']
                print(f"  Increasing agents to {num_agents} for {shift_type} Shift ({shift_result['start_time']}-{shift_result['end_time']}): "
                        f"{result['service_level']:.1f}% service level, {result['calls_arrived']} Calls arrived, {result['calls_handled']} Calls handled,"
                        f"{result['calls_abandoned']} Calls abandoned, {result['avg_wait']:.1f}s Avg wait, {result['max_wait']:.1f}s Max wait")
        
        # Store the results for this day
        results[day] = day_results

        # Calculate day summary
        day_calls = sum(r["calls_arrived"] for r in day_results)
        day_handled = sum(r["calls_handled"] for r in day_results)
        day_abandoned = sum(r["calls_abandoned"] for r in day_results)
        day_sl = np.mean([r["service_level"]
                         for r in day_results if r["calls_handled"] > 0])

        print(f"\n{day} Summary: {day_calls} calls, "
              f"{day_handled} handled, "
              f"{day_abandoned} abandoned/Not Answered, "
              f"{day_sl:.1f}% service level, "
              f"total_agents = {sum(r['agents'] for r in day_results)}")
        


    # Calculate weekly summary
    all_shifts = [shift for day_shifts in results.values()
                  for shift in day_shifts]
    weekly_calls = sum(shift["calls_arrived"] for shift in all_shifts)
    weekly_handled = sum(shift["calls_handled"] for shift in all_shifts)
    weekly_abandoned = sum(shift["calls_abandoned"] for shift in all_shifts)
    weekly_sl = np.mean([shift["service_level"]
                        for shift in all_shifts if shift["calls_handled"] > 0])

    print(f"\nWeekly Summary: {weekly_calls} calls, "
          f"{weekly_handled} handled, "
          f"{weekly_abandoned} abandoned/Not Answered, "
          f"{weekly_sl:.1f}% service level")
    
    # import json
    # print("\nFull results structure:")
    # print(json.dumps(results, indent=2))
    
    return results



