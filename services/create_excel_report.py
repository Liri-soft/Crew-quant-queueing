import pandas as pd
import numpy as np 
import services.erlang_staffing as erlang_staffing
import services.shift_optimizer as shift_optimizer
import os
import config_variables.config as config_module  # Import config to access call volume data


def create_excel_report(staffing_needs, ideal_pattern, simulation_results=None):    
    """
    Create a comprehensive Excel report with all staffing data and shift information

    Parameters:
    staffing_needs (dict): Dictionary with staffing needs for each day and hour
    ideal_pattern (dict): Dictionary with optimal shift pattern for the week
    simulation_results (dict, optional): Results from the shift simulation
    """
    print("\nCreating Excel report...")

    # Create a new Excel writer
    excel_path = 'StaffingReport.xlsx'
    writer = pd.ExcelWriter(excel_path, engine='openpyxl')

    # ----------------- SHEET 1: CALL VOLUME AND CONFIGURATION -----------------
    
    # Create sheet for call volume and configuration
    sheet_name = 'Call Volume & Config'
    
    # Create call volume section
    hours = list(range(erlang_staffing.HOURS_PER_DAY))
    call_volume_df = pd.DataFrame(index=hours)
    
    # Add call volume data for each day
    for day in erlang_staffing.DAYS_OF_WEEK:
        if day in config_module.CALL_VOLUME:
            call_volume_df[day] = config_module.CALL_VOLUME[day]
        else:
            call_volume_df[day] = [0] * len(hours)
    
    # Add time labels for easier reading
    call_volume_df.index = [f"{hour}:00" for hour in hours]
    call_volume_df.index.name = "Hour"
    
    # Add call volume totals
    call_volume_df['Daily Total'] = call_volume_df.sum(axis=1)
    call_volume_df.loc['Day Total'] = call_volume_df.sum()
    
    # Write title and call volume to sheet
    pd.DataFrame([{'Call Volume by Day and Hour': ''}]).to_excel(
        writer, sheet_name=sheet_name, index=False)
    call_volume_df.to_excel(writer, sheet_name=sheet_name, startrow=2)
    
    # Create configuration section
    config_data = {
        'Parameter': [
            'Shift Hours',
            'Agent Efficiency (%)',
            'Average Handling Time (min)',
            'Average Patience (sec)',
            'Target SLA Time (sec)',
            'Desired Service Level (%)',
            'Min After Call Work (sec)',
            'Max After Call Work (sec)',
            'Lunch Break Time (min)',
            'Max % Agents on Break'
        ],
        'Value': [
            config_module.SHIFT_HOURS,
            config_module.AGENT_EFFICIENCY,
            config_module.AVG_HANDLING_TIME,
            config_module.AVG_PATIENCE,
            config_module.TARGET_SLA,
            config_module.DESIRED_SLA,
            config_module.ACW_MIN,
            config_module.ACW_MAX,
            config_module.LUNCH_BREAK_TIME,
            config_module.MAX_PERCENTAGE_AGENTS_ON_BREAK
        ]
    }
    
    config_df = pd.DataFrame(config_data)
    
    # Write configuration title and data
    pd.DataFrame([{'Configuration Parameters': ''}]).to_excel(
        writer, sheet_name=sheet_name, startrow=call_volume_df.shape[0] + 5, index=False)
    config_df.to_excel(writer, sheet_name=sheet_name, 
                     startrow=call_volume_df.shape[0] + 7, index=False)

    # ----------------- SHEET 2: HOURLY STAFFING NEEDS -----------------
    
    # Create a sheet for hourly staffing needs
    staffing_df = pd.DataFrame(index=hours)

    for day in erlang_staffing.DAYS_OF_WEEK:
        staffing_df[day] = staffing_needs[day]

    # Add time labels for easier reading
    staffing_df.index = [f"{hour}:00" for hour in hours]
    staffing_df.index.name = "Hour"

    # Save to Excel sheet
    staffing_df.to_excel(writer, sheet_name='Hourly Staffing Needs')

    # ----------------- SHEET 3: IDEAL PATTERN -----------------
    
    if ideal_pattern:
        # Create summary table for the ideal pattern
        ideal_summary = pd.DataFrame([{
            'Pattern Number': ideal_pattern['pattern_number'],
            'Total Weekly Agents': ideal_pattern['total_weekly_agents'],
            'Total Weekly Hours': ideal_pattern['total_weekly_hours'],
            'Average Utilization (%)': ideal_pattern['avg_utilization']
        }])
        
        # Create shift times table
        shift_times_data = []
        for i, shift_time in enumerate(ideal_pattern['shift_times']):
            shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
            shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
            shift_times_data.append({
                'Shift': shift_type,
                'Time': shift_time
            })
        shift_times_df = pd.DataFrame(shift_times_data)
        
        # Create daily breakdown table
        daily_data = []
        for day_stat in ideal_pattern['daily_stats']:
            day_info = {
                'Day': day_stat['day'],
                'Total Agents': day_stat['agents'],
                'Agent Hours': day_stat['hours'],
                'Utilization (%)': day_stat['utilization']
            }
            
            # Add shift details
            for i, shift in enumerate(day_stat['shifts']):
                shift_names = ["First", "Second", "Third", "Fourth", "Fifth"]
                shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
                agents = shift['agents_needed']
                agent_hours = shift['agent_hours']
                
                day_info[f'{shift_type} Shift Agents'] = agents
                day_info[f'{shift_type} Shift Hours'] = agent_hours
                
            daily_data.append(day_info)
            
        daily_df = pd.DataFrame(daily_data)
        
        # Write to Excel with appropriate spacing
        pd.DataFrame([{'Ideal Weekly Shift Pattern': ''}]).to_excel(
            writer, sheet_name='Ideal Pattern', index=False)
        
        ideal_summary.to_excel(writer, sheet_name='Ideal Pattern', 
                              startrow=2, index=False)
        
        # Add shift times table a few rows below
        pd.DataFrame([{'Shift Times': ''}]).to_excel(
            writer, sheet_name='Ideal Pattern', startrow=ideal_summary.shape[0] + 4, index=False)
            
        shift_times_df.to_excel(writer, sheet_name='Ideal Pattern', 
                              startrow=ideal_summary.shape[0] + 6, index=False)
        
        # Add daily breakdown table a few rows below that
        pd.DataFrame([{'Daily Breakdown': ''}]).to_excel(
            writer, sheet_name='Ideal Pattern', 
            startrow=ideal_summary.shape[0] + shift_times_df.shape[0] + 8, index=False)
            
        daily_df.to_excel(writer, sheet_name='Ideal Pattern', 
                        startrow=ideal_summary.shape[0] + shift_times_df.shape[0] + 10, index=False)

    # ----------------- SHEET 4: ERLANG C SIMULATION -----------------
    erlang_results = None
    # Add Erlang C simulation results if available
    if simulation_results and 'erlang_results' in simulation_results:
        erlang_results = simulation_results['erlang_results']
        add_erlang_simulation_to_excel(writer, erlang_results)

    # ----------------- SHEET 5: FINAL SIMULATION -----------------
    
    # Add final simulation results if available
    if simulation_results and 'final_results' in simulation_results:
        add_final_simulation_to_excel(writer, simulation_results['final_results'], erlang_results)

    # Save and close the Excel file
    writer.close()

    print(f"Excel report saved to {excel_path}")
    return excel_path


def add_erlang_simulation_to_excel(writer, erlang_results):
    """
    Add Erlang C simulation results to the Excel report
    
    Parameters:
    writer: Excel writer object
    erlang_results (dict): Erlang C results from shift simulation
    """
    # Collect all shifts in a single list
    all_shifts = []
    
    for day, day_results in erlang_results.items():
        for shift in day_results:
            shift_data = {
                'Day': day,
                'Shift Type': shift['shift_type'],
                'Start Time': shift['start_time'],
                'End Time': shift['end_time'],
                'Hours Covered': ','.join(str(h) for h in shift['hours']) if 'hours' in shift else '',
                'Agents': shift['agents'],
                'Expected Calls': shift['calls_expected'],
                'Actual Calls': shift['calls_arrived'],
                'Calls Handled': shift['calls_handled'],
                'Calls Abandoned': shift['calls_abandoned'],
                'Average Wait (sec)': round(shift['avg_wait'], 1),
                'Maximum Wait (sec)': round(shift['max_wait'], 1),
                'Service Level (%)': round(shift['service_level'], 1),
            }
            all_shifts.append(shift_data)
    
    # Create a single DataFrame with all shifts and save to Excel
    all_shifts_df = pd.DataFrame(all_shifts)
    
    # Write title and data
    pd.DataFrame([{'Erlang C Simulation Results (Initial Staffing)': ''}]).to_excel(
        writer, sheet_name='Erlang C Simulation', index=False)
    all_shifts_df.to_excel(writer, sheet_name='Erlang C Simulation', startrow=2, index=False)
    
    # Create a simulation summary
    summary_data = []
    for day, day_results in erlang_results.items():
        day_calls = sum(r["calls_arrived"] for r in day_results)
        day_handled = sum(r["calls_handled"] for r in day_results)
        day_abandoned = sum(r["calls_abandoned"] for r in day_results)
        day_sl = np.mean([r["service_level"] for r in day_results if r["calls_handled"] > 0])
        total_agents = sum(r["agents"] for r in day_results)
        
        # Get expected call volume for this day
        expected_call_volume = sum(config_module.CALL_VOLUME.get(day, [0]*24))
        
        summary_data.append({
            'Day': day,
            'Expected Calls': expected_call_volume,
            'Actual Calls': day_calls,
            'Calls Handled': day_handled,
            'Calls Abandoned': day_abandoned,
            'Abandoned (%)': round((day_abandoned / day_calls * 100), 1) if day_calls > 0 else 0,
            'Service Level (%)': round(day_sl, 1),
            'Total Agents': total_agents
        })
    
    # Add weekly total
    all_day_expected = sum(d['Expected Calls'] for d in summary_data)
    all_day_calls = sum(d['Actual Calls'] for d in summary_data)
    all_day_handled = sum(d['Calls Handled'] for d in summary_data)
    all_day_abandoned = sum(d['Calls Abandoned'] for d in summary_data)
    all_day_sl = np.mean([d['Service Level (%)'] for d in summary_data])
    all_agents = sum(d['Total Agents'] for d in summary_data)
    
    summary_data.append({
        'Day': 'WEEKLY TOTAL',
        'Expected Calls': all_day_expected,
        'Actual Calls': all_day_calls,
        'Calls Handled': all_day_handled,
        'Calls Abandoned': all_day_abandoned,
        'Abandoned (%)': round((all_day_abandoned / all_day_calls * 100), 1) if all_day_calls > 0 else 0,
        'Service Level (%)': round(all_day_sl, 1),
        'Total Agents': all_agents
    })

    summary_df = pd.DataFrame(summary_data)
    
    # Write summary title and data
    pd.DataFrame([{'Erlang C Simulation Summary': ''}]).to_excel(
        writer, sheet_name='Erlang C Simulation', 
        startrow=all_shifts_df.shape[0] + 5, index=False)
    summary_df.to_excel(writer, sheet_name='Erlang C Simulation', 
                       startrow=all_shifts_df.shape[0] + 7, index=False)


def add_final_simulation_to_excel(writer, final_results, erlang_results=None):
    """
    Add final simulation results to the Excel report
    
    Parameters:
    writer: Excel writer object
    final_results (dict): Final results from shift simulation
    erlang_results (dict, optional): Erlang C results for comparison
    """
    # Collect all shifts in a single list
    all_shifts = []
    
    for day, day_results in final_results.items():
        for shift in day_results:
            shift_data = {
                'Day': day,
                'Shift Type': shift['shift_type'],
                'Start Time': shift['start_time'],
                'End Time': shift['end_time'],
                'Hours Covered': ','.join(str(h) for h in shift['hours']) if 'hours' in shift else '',
                'Agents': shift['agents'],
                'Expected Calls': shift['calls_expected'],
                'Actual Calls': shift['calls_arrived'],
                'Calls Handled': shift['calls_handled'],
                'Calls Abandoned': shift['calls_abandoned'],
                'Average Wait (sec)': round(shift['avg_wait'], 1),
                'Maximum Wait (sec)': round(shift['max_wait'], 1),
                'Service Level (%)': round(shift['service_level'], 1),
            }
            all_shifts.append(shift_data)
    
    # Create a single DataFrame with all shifts and save to Excel
    all_shifts_df = pd.DataFrame(all_shifts)
    
    # Write title and data
    pd.DataFrame([{'Final Simulation Results (Optimized Staffing)': ''}]).to_excel(
        writer, sheet_name='Final Simulation', index=False)
    all_shifts_df.to_excel(writer, sheet_name='Final Simulation', startrow=2, index=False)
    
    # Create a simulation summary
    summary_data = []
    for day, day_results in final_results.items():
        day_calls = sum(r["calls_arrived"] for r in day_results)
        day_handled = sum(r["calls_handled"] for r in day_results)
        day_abandoned = sum(r["calls_abandoned"] for r in day_results)
        day_sl = np.mean([r["service_level"] for r in day_results if r["calls_handled"] > 0])
        total_agents = sum(r["agents"] for r in day_results)
        
        # Get expected call volume for this day
        expected_call_volume = sum(config_module.CALL_VOLUME.get(day, [0]*24))
        
        summary_data.append({
            'Day': day,
            'Expected Calls': expected_call_volume,
            'Actual Calls': day_calls,
            'Calls Handled': day_handled,
            'Calls Abandoned': day_abandoned,
            'Abandoned (%)': round((day_abandoned / day_calls * 100), 1) if day_calls > 0 else 0,
            'Service Level (%)': round(day_sl, 1),
            'Total Agents': total_agents
        })
    
    # Add weekly total
    all_day_expected = sum(d['Expected Calls'] for d in summary_data)
    all_day_calls = sum(d['Actual Calls'] for d in summary_data)
    all_day_handled = sum(d['Calls Handled'] for d in summary_data)
    all_day_abandoned = sum(d['Calls Abandoned'] for d in summary_data)
    all_day_sl = np.mean([d['Service Level (%)'] for d in summary_data])
    all_agents = sum(d['Total Agents'] for d in summary_data)
    
    summary_data.append({
        'Day': 'WEEKLY TOTAL',
        'Expected Calls': all_day_expected,
        'Actual Calls': all_day_calls,
        'Calls Handled': all_day_handled,
        'Calls Abandoned': all_day_abandoned,
        'Abandoned (%)': round((all_day_abandoned / all_day_calls * 100), 1) if all_day_calls > 0 else 0,
        'Service Level (%)': round(all_day_sl, 1),
        'Total Agents': all_agents
    })

    summary_df = pd.DataFrame(summary_data)
    
    # Write summary title and data
    pd.DataFrame([{'Final Simulation Summary': ''}]).to_excel(
        writer, sheet_name='Final Simulation', 
        startrow=all_shifts_df.shape[0] + 5, index=False)
    summary_df.to_excel(writer, sheet_name='Final Simulation', 
                       startrow=all_shifts_df.shape[0] + 7, index=False)
    
    # Add comparison section - difference between Erlang C and Final
    if erlang_results:
        pd.DataFrame([{'Staffing Comparison (Final vs Erlang C)': ''}]).to_excel(
            writer, sheet_name='Final Simulation', 
            startrow=all_shifts_df.shape[0] + summary_df.shape[0] + 10, index=False)
            
        compare_data = []
        for i, row in enumerate(summary_data):
            if i < len(summary_data) - 1:  # Skip the weekly total row for now
                day = row['Day']
                
                # Calculate Erlang C metrics for this day
                erlang_agents = 0
                erlang_sl = 0
                
                if day in erlang_results:
                    erlang_agents = sum(s['agents'] for s in erlang_results[day])
                    erlang_sl_values = [s['service_level'] for s in erlang_results[day] if s['calls_handled'] > 0]
                    erlang_sl = np.mean(erlang_sl_values) if erlang_sl_values else 0
                
                # Final simulation metrics
                final_agents = row['Total Agents']
                final_sl = row['Service Level (%)']
                
                compare_data.append({
                    'Day': day,
                    'Erlang C Agents': erlang_agents,
                    'Final Agents': final_agents,
                    'Additional Agents': final_agents - erlang_agents,
                    'Erlang C SL (%)': round(erlang_sl, 1),
                    'Final SL (%)': final_sl,
                    'SL Improvement (%)': round(final_sl - erlang_sl, 1)
                })
        
        # Add weekly total
        compare_data.append({
            'Day': 'WEEKLY TOTAL',
            'Erlang C Agents': sum(r['Erlang C Agents'] for r in compare_data),
            'Final Agents': sum(r['Final Agents'] for r in compare_data),
            'Additional Agents': sum(r['Additional Agents'] for r in compare_data),
            'Erlang C SL (%)': round(np.mean([r['Erlang C SL (%)'] for r in compare_data]), 1),
            'Final SL (%)': round(np.mean([r['Final SL (%)'] for r in compare_data]), 1),
            'SL Improvement (%)': round(np.mean([r['SL Improvement (%)'] for r in compare_data]), 1)
        })
        
        compare_df = pd.DataFrame(compare_data)
        compare_df.to_excel(writer, sheet_name='Final Simulation', 
                           startrow=all_shifts_df.shape[0] + summary_df.shape[0] + 12, index=False)


if __name__ == "__main__":
    print("To generate an Excel report, run main.py")