import simpy
import numpy as np
import random
from erlang_staffing import arrival_rate_urgent, URGENT_TASK_WORK_MINUTES, DAYS_OF_WEEK, HOURS_PER_DAY

# Convert minutes to seconds for simulation
AHT = URGENT_TASK_WORK_MINUTES * 60  # Average handling time in seconds
SIM_DURATION = 3600  # seconds (1 hour)
TARGET_SLA = 20  # Target answer time in seconds for service level calculation


def run_simulation(num_agents, arrival_rate_per_hour, service_time_seconds=AHT):
   
    
    if arrival_rate_per_hour == 0:
        return {
            "calls_arrived": 0,
            "calls_handled": 0,
            "calls_expected": 0,
            "avg_wait": 0,
            "max_wait": 0,
            "service_level": 100,
            "wait_times": []
        }


    # Setup simulation
    env = simpy.Environment()
    agents = simpy.Resource(env, capacity=num_agents)
    
    wait_times = []
    calls_handled = 0
    calls_arrived = 0 

    # Number of calls to generate
    NUM_CALLS = int(arrival_rate_per_hour)

    def call_generator(env, agents):
        nonlocal calls_arrived
        
        arrival_times = np.sort(np.random.uniform(0, SIM_DURATION, NUM_CALLS))
        # print(f"arrrival time: {arrival_times}")
        last_time = 0
        for i, scheduled_time in enumerate(arrival_times):
            yield env.timeout(scheduled_time - last_time)
            calls_arrived += 1
            env.process(handle_call(env, agents))
            # print(f"call {i+1} generated at {env.now} seconds")
            last_time = scheduled_time 

    def handle_call(env, agents):
        """Handle an incoming call"""
        nonlocal calls_handled
        arrival_time = env.now

        with agents.request() as req:
            yield req

            # Calculate wait time
            wait = env.now - arrival_time
            wait_times.append(wait)

            # Count handled call
            calls_handled += 1

            # Simulate service time
            yield env.timeout(service_time_seconds)

            

    # Start the call generation process
    env.process(call_generator(env, agents))

    # Run the simulation for one hour
    env.run(until=SIM_DURATION)

    # Analyze Results
    if len(wait_times) > 0:
        wait_array = np.array(wait_times)
        avg_wait = np.mean(wait_array)
        max_wait = np.max(wait_array)
        # Service level: percentage of calls answered within target time
        service_level = np.mean(wait_array <= TARGET_SLA) * 100
    else:
        avg_wait = 0
        max_wait = 0
        service_level = 100

    return {
        "calls_arrived": calls_arrived,
        "calls_handled": calls_handled,
        "calls_expected": arrival_rate_per_hour,
        "avg_wait": avg_wait,
        "max_wait": max_wait,
        "service_level": service_level,
        "wait_times": wait_times
    }


def simulate_staffing_plan(staffing_needs):
    
    all_results = []

    for day in DAYS_OF_WEEK:
        day_results = []
        print(f"\nSimulating {day}:")

        for hour in range(HOURS_PER_DAY):
            num_agents = staffing_needs[day][hour]
            arrival_rate = arrival_rate_urgent[day][hour]

            # Run the simulation
            # Store the result
            result = run_simulation(num_agents, arrival_rate)
            simulation_result = {
                "day": day,
                "hour": hour,
                "calls_expected": arrival_rate,
                "calls_arrived": result["calls_arrived"],
                "calls_handled": result["calls_handled"],
                "agents": num_agents,
                "avg_wait": result["avg_wait"],
                "max_wait": result["max_wait"],
                "service_level": result["service_level"],
                "wait_times": result["wait_times"]
            }

            day_results.append(simulation_result)

            # Print progress
            print(f"Hour {hour:2d}: {result['calls_arrived']} calls arrived, {result['calls_handled']:3.0f} handled, "
                  f"{result['avg_wait']:5.1f}s avg wait, "
                  f"{result['service_level']:5.1f}% SL with {num_agents} agents")

        all_results.extend(day_results)

        # Calculate day summary
        day_calls = sum(r["calls_handled"] for r in day_results)
        day_agents = sum(r["agents"] for r in day_results)
        day_sl = np.mean([r["service_level"]
                         for r in day_results if r["calls_handled"] > 0])

        print(f"\n{day} Summary: {day_calls:.0f} calls, {day_agents} agent hours, "
              f"{day_sl:.1f}% service level")

    # Calculate overall statistics
    total_calls = sum(r["calls_handled"] for r in all_results)
    total_agents = sum(r["agents"] for r in all_results)
    overall_sl = np.mean([r["service_level"]
                         for r in all_results if r["calls_handled"] > 0])

    print("\nOverall Weekly Statistics:")
    print(f"Total calls handled: {total_calls:.0f}")
    print(f"Total agent hours: {total_agents}")
    print(f"Overall service level: {overall_sl:.1f}%")

    return all_results
