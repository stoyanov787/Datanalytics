# conda run -n {env} python main.py --project {project_name} --data_prep_module standard
# conda run -n {env} python main.py --project {project_name} --train_module standard
# conda run -n {env} python main.py --project {project_name} --eval_module standard --session "{session_id}""

"""
This is a program that simulates how gizmo works because gizmo is a proprietary software of Postbank Data Analytics team.
This program is a simulation of the gizmo software and it is used to show how the complete project works which is specifically built for gizmo.
"""
import os
import sys
import time
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def main(timeout: int = 60):
    """
    This is the main function that is used to simulate the gizmo software.
    This function is used to simulate the gizmo software and it is used to show how the complete project works which is specifically built for gizmo.

    :param timeout: Timeout for the main function
    :type timeout: int
    :return: None
    """
    logger.info("Starting gizmo main function")
    logger.info("Arguments passed to the main function: %s", sys.argv)

    try:
        if len(sys.argv) not in (5, 6):
            logger.warning("Invalid number of arguments passed to the main function")
            raise ValueError("Invalid number of arguments passed to the main function")
        if sys.argv[1] != "--project":
            logger.warning("Invalid argument passed to the main function")
            raise ValueError("Invalid argument passed to the main function")
        
        project_name = sys.argv[2]
        project_path = os.path.join("input_data", project_name)
        if os.path.isfile(project_path) is None:
            logger.warning("Project name is not valid")
            raise ValueError("Project name is not valid")
        
        if sys.argv[3] == "--data_prep_module":
            if sys.argv[4] == "standard":
                logger.info("Data preparation module is standard")
            else:
                logger.warning("Invalid argument passed to the main function")
                raise ValueError("Invalid argument passed to the main function")
            time.sleep(timeout)
            output_project_path = os.path.join("output_data", project_name)
            os.mkdir(output_project_path)
            logger.info("Data preparation completed successfully")

            
        elif sys.argv[3] == "--train_module":
            logger.info("Training module is standard")
        elif sys.argv[3] == "--eval_module":
            logger.info("Evaluation module is standard")
        else:
            logger.warning("Invalid argument passed to the main function")
            raise ValueError("Invalid argument passed to the main function")
    except Exception as e:
        logger.exception("Error in main function")
        sys.exit(1)
    
if __name__ == "__main__":
    main()
