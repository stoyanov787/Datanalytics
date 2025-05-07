"""
This is a program that simulates how gizmo works because gizmo is a proprietary software of Postbank Data Analytics team.
This program is a simulation of the gizmo software and it is used to show how the complete project works which is specifically built for gizmo.
The commands that are used for gizmo are:
- conda run -n {env} python main.py --project {project_name} --data_prep_module standard
- conda run -n {env} python main.py --project {project_name} --train_module standard
- conda run -n {env} python main.py --project {project_name} --eval_module standard --session "{session_id}"
"""

import os
import sys
from time import sleep
from datetime import datetime
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
    ]
)

logger = logging.getLogger(__name__)

INPUT_DATA_DIR = os.path.join(os.getcwd(), "input_data")
OUTPUT_DATA_DIR = os.path.join(os.getcwd(), "output_data")
SESSION_DATA_DIR = os.path.join(os.getcwd(), "sessions")


def setup_directories() -> None:
    """Ensure required directories exist."""
    for directory in [INPUT_DATA_DIR, OUTPUT_DATA_DIR, SESSION_DATA_DIR]:
        if not os.path.exists(directory):
            os.mkdir(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")


def validate_arguments(expected_arg_count: int) -> None:
    """Validate the number of arguments passed to the script."""
    if len(sys.argv) != expected_arg_count:
        logger.warning("Invalid number of arguments passed to the main function")
        raise ValueError("Invalid number of arguments passed to the main function")


def validate_project_name(project_name: str) -> str:
    """Validate the project name."""
    project_path = os.path.join(INPUT_DATA_DIR, project_name)
    if not os.path.exists(project_path):
        logger.warning(f"Project name '{project_name}' is not valid")
        raise ValueError("Project name is not valid")
    logger.info(f"Validated project name: {project_name}")
    return project_path


def handle_data_prep(project_name: str, timeout:int) -> None:
    """Handle the data preparation module."""
    logger.info("Starting data preparation module")
    sleep(timeout)

    output_project_path = os.path.join(OUTPUT_DATA_DIR, project_name)
    if not os.path.exists(output_project_path):
        os.mkdir(output_project_path)
        logger.info(f"Created output directory for data preparation: {output_project_path}")
    else:
        logger.info(f"Directory already exists: {output_project_path}")
    logger.info("Data preparation completed successfully")


def handle_training(project_name: str, timeout: int) -> None:
    """Handle the training module."""
    logger.info("Starting training module")
    sleep(timeout)

    output_project_path = os.path.join(SESSION_DATA_DIR, f"TRAIN_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    if not os.path.exists(output_project_path):
        os.mkdir(output_project_path)
        logger.info(f"Created training session directory: {output_project_path}")
    else:
        logger.info(f"Directory already exists: {output_project_path}")
    logger.info("Training completed successfully")


def handle_evaluation(session: str) -> None:
    """Handle the evaluation module."""
    logger.info("Starting evaluation module")
    session_path = os.path.join(SESSION_DATA_DIR, session)
    if not os.path.exists(session_path):
        logger.warning(f"Session '{session}' is not valid")
        raise ValueError("Session is not valid")

    output_project_path = os.path.join(SESSION_DATA_DIR, session.replace("TRAIN", "EVAL"))
    if not os.path.exists(output_project_path):
        os.mkdir(output_project_path)
        logger.info(f"Created evaluation output directory: {output_project_path}")
    logger.info("Evaluation completed successfully")


def main(timeout: int = 5) -> None:
    """
    This is the main function that is used to simulate the gizmo software.

    :param timeout: Timeout for the main function
    :type timeout: int
    :return: None
    """
    logger.info("Starting gizmo main function")
    logger.info("Arguments passed to the main function: %s", sys.argv)

    setup_directories()

    try:
        if len(sys.argv) < 5:
            validate_arguments(5)

        if sys.argv[1] != "--project":
            logger.warning("Invalid argument passed to the main function")
            raise ValueError("Invalid argument passed to the main function")

        project_name = sys.argv[2]
        validate_project_name(project_name)

        module_type = sys.argv[3]
        if module_type == "--data_prep_module":
            if sys.argv[4] == "standard":
                handle_data_prep(project_name, timeout)
            else:
                raise ValueError("Invalid argument for data preparation module")

        elif module_type == "--train_module":
            if sys.argv[4] == "standard":
                handle_training(project_name, timeout)
            else:
                raise ValueError("Invalid argument for training module")

        elif module_type == "--eval_module":
            if sys.argv[4] == "standard" and sys.argv[5] == "--session":
                session = sys.argv[6]
                handle_evaluation(session)
            else:
                raise ValueError("Invalid argument for evaluation module")

        else:
            logger.warning("Invalid module type passed to the main function")
            raise ValueError("Invalid module type passed to the main function")

    except ValueError as e:
        logger.exception("Error in main function")
        sys.exit(1)


if __name__ == "__main__":
    main()
