# conda run -n {env} python main.py --project {project_name} --data_prep_module standard
# conda run -n {env} python main.py --project {project_name} --train_module standard
# conda run -n {env} python main.py --project {project_name} --eval_module standard --session "{session_id}""

"""
This is a program that simulates how gizmo works because gizmo is a proprietary software of Postbank Data Analytics team.
This program is a simulation of the gizmo software and it is used to show how the complete project works which is specifically built for gizmo.
"""

import os
import sys
from time import sleep
from datetime import datetime
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

INPUT_DATA_DIR = os.path.join(os.getcwd(), "input_data")
OUTPUT_DATA_DIR = os.path.join(os.getcwd(), "output_data")
SESSION_DATA_DIR = os.path.join(os.getcwd(), "session")
if not os.path.exists(INPUT_DATA_DIR):
    os.mkdir(INPUT_DATA_DIR)
if not os.path.exists(OUTPUT_DATA_DIR):
    os.mkdir(OUTPUT_DATA_DIR)
if not os.path.exists(SESSION_DATA_DIR):
    os.mkdir(SESSION_DATA_DIR)

def main(timeout: int = 5) -> None:
    """
    This is the main function that is used to simulate the gizmo software.
    This function is used to simulate the gizmo software and it is used to show how the complete project works which is specifically built for gizmo.

    :param timeout: Timeout for the main function
    :type timeout: int
    :return: None
    """
    logger.info("Starting gizmo main function")
    logger.info("Arguments passed to the main function: %s", sys.argv)

#{train_or_eval}_{project_name}

    print(sys.argv)
    try:
        if len(sys.argv) not in (5, 7):
            logger.warning("Invalid number of arguments passed to the main function")
            raise ValueError("Invalid number of arguments passed to the main function")
        if sys.argv[1] != "--project":
            logger.warning("Invalid argument passed to the main function")
            raise ValueError("Invalid argument passed to the main function")
        
        project_name = sys.argv[2]
        project_path = os.path.join(INPUT_DATA_DIR, project_name)
        if not os.path.exists(project_path):
            logger.warning("Project name is not valid")
            raise ValueError("Project name is not valid")
        
        if sys.argv[3] == "--data_prep_module":
            if sys.argv[4] == "standard":
                logger.info("Data preparation module is standard")
            else:
                logger.warning("Invalid argument passed to the main function")
                raise ValueError("Invalid argument passed to the main function")
            sleep(timeout)

            output_project_path = os.path.join(OUTPUT_DATA_DIR, project_name)
            if not os.path.exists(output_project_path):
                os.mkdir(output_project_path)
            else:
                logger.info(f"Directory already exists: {output_project_path}")
            logger.info("Data preparation completed successfully")

            
        elif sys.argv[3] == "--train_module":
            if sys.argv[4] == "standard":
                logger.info("Training module is standard")
            else:
                logger.warning("Invalid argument passed to the main function")
                raise ValueError("Invalid argument passed to the main function")
            sleep(timeout)

            output_project_path = os.path.join(SESSION_DATA_DIR, f"TRAIN_{project_name}_{datetime.now()}")
            if not os.path.exists(output_project_path):
                os.mkdir(output_project_path)
            else:
                logger.info(f"Directory already exists: {output_project_path}")
            logger.info("Training completed successfully")


            
        elif sys.argv[3] == "--eval_module":
            logger.info("Evaluation module is standard")
            if sys.argv[4] == "standard":
                if sys.argv[5] == "--session":
                    session_id = sys.argv[6]
                    logger.info("Session ID is: %s", session_id)
                    # finish it
                else:
                    logger.warning("Invalid argument passed to the main function")
                    raise ValueError("Invalid argument passed to the main function")
            else:
                logger.warning("Invalid argument passed to the main function")
                raise ValueError("Invalid argument passed to the main function")
        else:
            logger.warning("Invalid argument passed to the main function")
            raise ValueError("Invalid argument passed to the main function")
    except ValueError as e:
        logger.exception("Error in main function")
        sys.exit(1)
    
if __name__ == "__main__":
    main()
