# Datanalytics

A data analytics platform built for Postbank's Data Analytics Department, featuring AI-powered predictions and data processing capabilities.

![Screenshot 2025-02-01 141852](https://github.com/user-attachments/assets/2cdd09ec-6cc9-4eb0-9453-74a7bd97171d)
![Screenshot 2025-02-01 165837](https://github.com/user-attachments/assets/0b22bcc8-f68f-43f2-8af6-4c44a891a303)
![Screenshot 2025-02-01 170259](https://github.com/user-attachments/assets/8ece29e2-8a03-40ff-8200-2bfdb12c324d)
![Screenshot 2025-02-01 170648](https://github.com/user-attachments/assets/aa8d4bdb-8abc-4a68-bf12-91705e358488)
![Screenshot 2025-02-01 170932](https://github.com/user-attachments/assets/6954d141-7cbb-4fe2-a16c-2711bb3c8222)
![Screenshot 2025-02-01 171553](https://github.com/user-attachments/assets/41d3f295-5d03-47c1-b02e-0397fa12bc1f)
![Screenshot 2025-02-01 171912](https://github.com/user-attachments/assets/2b7fcff5-8a90-4320-9e9e-7783130df8b0)
![Screenshot 2025-02-01 172029](https://github.com/user-attachments/assets/31932159-2ad3-4b92-bf61-72b7dc040f9b)



## What is Datanalytics?

Datanalytics is a web-based platform that allows data analysts to upload CSV datasets, configure analysis parameters, and run machine learning pipelines. The platform provides an intuitive interface for managing data science projects from data preparation to model evaluation and reporting.

## About the Developer

This project was developed by **Georgi Stoyanov** as a project for **Technology School Electronic Systems (TUES), associated with Technical University-Sofia**.

## What is Gizmo?

Gizmo is a simulated proprietary AI engine that represents Postbank's data analytics capabilities. In this educational project, Gizmo is implemented as a Python script that demonstrates:

- Automated data preparation workflows
- Machine learning model training (XGBoost, Logistic Regression, Decision Trees, Random Forest)
- Model evaluation and session management
- File-based input/output processing

The Gizmo simulation shows how enterprise AI systems might integrate with web platforms for data analytics workflows.

## Installation

### Prerequisites
- Docker
- Docker Compose

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/stoyanov787/Datanalytics.git
cd Datanalytics
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

3. **Ensure that entrypoint.sh is using LF encoding and NOT CRLF:**
- If you are using Windows or the entrypoint.sh is not in LF encoding, encode it in LF standard.

4. **Build and run:**
```bash
docker-compose up --build
```

5. **Access the application:**
- Web Interface: http://localhost:8000

## Features

- **Project Management**: Create and manage data analytics projects
- **CSV Upload**: Upload and validate datasets
- **Parameter Configuration**: Set analysis parameters and model cutoffs
- **Gizmo Integration**: Simulate enterprise AI processing
- **Report Generation**: Automated Sweetviz reports for data exploration
- **User Authentication**: Secure login system with email validation
- **Task Monitoring**: Real-time progress tracking for long-running processes

## Technology Stack

- **Backend**: Django 5.1.2, PostgreSQL, Celery, Redis
- **Frontend**: Bootstrap 5.3.6, JavaScript
- **AI Simulation**: Python, Pandas, Conda environment
- **Infrastructure**: Docker, Docker Compose

## License

This is an educational project developed for academic purposes at Technology School Electronic Systems (TUES), associated with Technical University-Sofia.

---

**Project by Georgi Stoyanov**  
**Technology School Electronic Systems (TUES), associated with Technical University-Sofia**
