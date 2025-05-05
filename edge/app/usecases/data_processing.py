from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData
from typing import Optional

MIN_DELTA = 2500         # ігнорувати взагалі все нижче 2.5k
THRESHOLD_BUMP = 8000    # bump — лише дуже різка зміна
THRESHOLD_POTHOLE = 16000 # pothole — ще рідкісніший, екстремальний стрибок


previous_z: Optional[float] = None

def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    global previous_z

    z = agent_data.accelerometer.z

    if previous_z is None:
        delta = 0.0
    else:
        delta = abs(z - previous_z)

    previous_z = z

    # Ігнорувати слабкі коливання
    if delta < MIN_DELTA:
        state = 'normal'
    elif delta > THRESHOLD_POTHOLE:
        state = 'pothole'
    elif delta > THRESHOLD_BUMP:
        state = 'bump'
    else:
        state = 'normal'

    return ProcessedAgentData(road_state=state, agent_data=agent_data)
