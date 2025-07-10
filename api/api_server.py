from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from fastapi.responses import FileResponse
import importlib
import os
import copy
import services.shift_optimizer
import services.ideal_shift
import services.shift_simulation
import services.erlang_staffing
import services.create_excel_report
from services.logging_config import setup_logger

# Set up logger for this module
logger = setup_logger(__name__)

router = APIRouter()


class ConfigInput(BaseModel):
    CALL_VOLUME: Dict[str, List[int]]
    SHIFT_HOURS: int
    AGENT_EFFICIENCY: int
    AVG_HANDLING_TIME: float
    AVG_PATIENCE: int
    TARGET_SLA: int
    DESIRED_SLA: int
    CALL_COMPLEXITY_DISTRIBUTION: Dict[str, Any]
    ACW_MIN: int
    ACW_MAX: int
    LUNCH_BREAK_TIME: int
    MAX_PERCENTAGE_AGENTS_ON_BREAK: int

@router.get("/")
def read_root():
    """Root endpoint to check if the API is running"""
    return {"message": "Welcome to the Crew Quant Queueing API!"}

@router.get("/download-excel")
def download_excel():
    """Download the generated Excel file"""
    file_path = 'StaffingReport.xlsx'

    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="StaffingReport.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        logger.error("Excel file not found. Run simulation first.")
        raise HTTPException(status_code=404, detail="Excel file not found. Run simulation first.")


@router.post("/simulate")
def simulate(config: ConfigInput):
    # Patch config values in memory
    try:
        import config_variables.config as config_module
        config_module.CALL_VOLUME = config.CALL_VOLUME
        config_module.SHIFT_HOURS = config.SHIFT_HOURS
        config_module.AGENT_EFFICIENCY = config.AGENT_EFFICIENCY
        config_module.AVG_HANDLING_TIME = config.AVG_HANDLING_TIME
        config_module.AVG_PATIENCE = config.AVG_PATIENCE
        config_module.TARGET_SLA = config.TARGET_SLA
        config_module.DESIRED_SLA = config.DESIRED_SLA
        config_module.CALL_COMPLEXITY_DISTRIBUTION = config.CALL_COMPLEXITY_DISTRIBUTION
        config_module.ACW_MIN = config.ACW_MIN
        config_module.ACW_MAX = config.ACW_MAX
        config_module.LUNCH_BREAK_TIME = config.LUNCH_BREAK_TIME
        config_module.MAX_PERCENTAGE_AGENTS_ON_BREAK = config.MAX_PERCENTAGE_AGENTS_ON_BREAK
            
        importlib.reload(services.erlang_staffing)
        importlib.reload(services.shift_optimizer)
        importlib.reload(services.ideal_shift)
        importlib.reload(services.shift_simulation)
            
        logger.info("Configuration values patched successfully")
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")

    # Run the simulation pipeline
    staffing_needs = services.erlang_staffing.calculate_hourly_staffing_needs()

    all_patterns = services.shift_optimizer.generate_shift_patterns()

    # Display the patterns using the function from shift_optimizer
    services.shift_optimizer.display_shift_patterns(all_patterns)
    # Display evaluations for all days and patterns
    services.shift_optimizer.display_pattern_evaluations(
        all_patterns, staffing_needs)

    ideal_pattern = services.ideal_shift.find_ideal_shift_pattern(staffing_needs)

    # Display the ideal pattern
    services.ideal_shift.display_ideal_shift_pattern(ideal_pattern)

    simulation_results = services.shift_simulation.simulate_ideal_pattern(
        ideal_pattern)
    
    graph_data = copy.deepcopy(simulation_results)


    # in final results, adding erlang_agents from erlang_results
    if 'erlang_results' in simulation_results and 'final_results' in simulation_results:
        # For each day and shift in final_results, add the erlang_agents value
        for day, day_shifts in simulation_results['final_results'].items():
            # Create a lookup map of erlang agents by shift type
            erlang_agents_by_shift = {}
            if day in simulation_results['erlang_results']:
                for erlang_shift in simulation_results['erlang_results'][day]:
                    # Create a key from shift_type, start_time, and end_time
                    shift_key = (
                        erlang_shift['shift_type'],
                        erlang_shift['start_time'],
                        erlang_shift['end_time']
                    )
                    erlang_agents_by_shift[shift_key] = erlang_shift['agents']

            # Add erlang_agents to each final shift
            for shift in day_shifts:
                shift_key = (shift['shift_type'],
                             shift['start_time'], shift['end_time'])
                if shift_key in erlang_agents_by_shift:
                    shift['erlang_agents'] = erlang_agents_by_shift[shift_key]
                else:
                    # If we can't find a direct match, try matching just by start/end time
                    matching_shifts = [
                        e_shift for e_shift in simulation_results['erlang_results'].get(day, [])
                        if e_shift['start_time'] == shift['start_time']
                        and e_shift['end_time'] == shift['end_time']
                    ]
                    if matching_shifts:
                        shift['erlang_agents'] = matching_shifts[0]['agents']
                    else:
                        # No match found, set to 0 or some default value
                        shift['erlang_agents'] = 0

    # Create Excel report
    services.create_excel_report.create_excel_report(
        staffing_needs, ideal_pattern, simulation_results)

    # Return results as JSON
    return {
        "simulation_results": simulation_results['final_results'],
        "graph_data": graph_data,
        "excel_download_url": "/download-excel"
    }
