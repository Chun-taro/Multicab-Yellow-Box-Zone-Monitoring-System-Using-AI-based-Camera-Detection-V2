# AI-Based Multicab Yellow Box Zone Violation Monitoring System Using Real-Time Camera Detection

## 1. INTRODUCTION
This section provides the background and rationale for the study, identifies the research problem, states the objectives, and discusses the significance and scope of the proposed AI-based multicab monitoring system.

### 1.1 Background of the Study
Traffic congestion and violations of road regulations remain significant challenges in many urban areas across the Philippines. With the continuous increase in vehicle volume, local government units (LGUs) struggle to maintain efficient traffic flow due to limited manpower and a heavy reliance on manual monitoring and enforcement methods (Department of Transportation [DOTr], 2023). Public transport vehicles, particularly **Multicabs**, are frequently observed committing traffic violations such as stopping or waiting for passengers within yellow box zones, prolonged loading and unloading at intersections, obstructing pedestrian crossings, and occupying restricted road spaces beyond allowable stop times. These improper road behaviors disrupt traffic movement, block intersecting lanes, and contribute to vehicle queuing, travel delays, and reduced road efficiency, especially in high-traffic intersections (Ho et al., 2019; Bhavsar et al., 2023; Rathore et al., 2021). 

In the context of Malaybalay City, preliminary observations conducted during peak hours reveal that multicab-related stopping violations occur repeatedly within short monitoring periods, with multiple instances witnessed daily at designated yellow box zones. Recent advancements in Artificial Intelligence (AI) and computer vision have enabled the development of AI-assisted systems capable of analyzing vehicle behavior through camera-based input. Studies have shown that deep learning models such as YOLO (You Only Look Once) can effectively detect and classify vehicles in real time, offering higher consistency compared to traditional observation methods (Valdivieso Tituana et al., 2022; Basheer Ahmed et al., 2023). 

The Traffic Management Center (TMC) of Malaybalay City currently relies on a combination of traffic personnel and limited Closed-Circuit Television (CCTV) monitoring. However, this approach restricts coverage and real-time response, particularly during peak hours (Malaybalay City Information Office, 2024). The absence of intelligent monitoring tools highlights the need for a system that can automatically observe Multicab activity and provide objective evidence for local traffic management efforts.

### Statement of the Problem
Despite the implementation of regulations, improper multicab behavior continues to be a persistent contributor to traffic congestion in Malaybalay City, particularly in yellow box zones located at busy intersections. Frequent violations such as prolonged stopping and loading within restricted zones disrupt traffic flow, delay commuters, and reduce overall road efficiency. 

The TMC currently relies on manual enforcement and limited CCTV monitoring, which constrains continuous observation and accurate documentation. These limitations make it difficult to consistently detect violations, objectively validate infractions, and promptly address congestion. Without an intelligent and technology-assisted monitoring mechanism, multicab-related violations are likely to persist, resulting in recurring congestion and limited availability of reliable data to support traffic planning.

This study seeks to address the following question:
**How can an AI-based system be developed to monitor multicab activity using camera input and provide real-time data to support traffic management and enforcement in Malaybalay City?**

### 1.2 Objectives of the Study
The main goal of this study is to enhance traffic management in Malaybalay City by developing an AI-based system capable of monitoring multicab activity in yellow box zones.

Specifically, the study aims to:
- Enable real-time detection and monitoring of multicabs entering and stopping in yellow box zones using YOLOv8.
- Implement an automated tracking mechanism to record multicab stop times and generate alerts for violations.
- Provide the Traffic Management Center (TMC) with an interactive web dashboard to review violations, access historical data, and support data-driven decision-making.
- Evaluate the system’s effectiveness in terms of monitoring accuracy, reliability, and usability under various traffic conditions.

### 1.3 Significance of the Study
This study will be significant to the **commuting public** of Malaybalay City, particularly daily passengers, students, and workers, by reducing delays and improving travel reliability. For **multicab drivers and operators**, the system provides objective evidence for violations, promoting fairer enforcement and encouraging compliance with traffic regulations. 

The **Traffic Management Center (TMC)** will gain a practical and scalable tool for real-time monitoring and automated reporting, enabling officers to focus enforcement efforts where they are most needed. **Local government units and policymakers** will benefit from accurate, longitudinal traffic data to inform future zoning decisions and public transport improvements. Finally, **future researchers** can use this project as a foundation for studies on AI-based monitoring in other local government applications.

### 1.4 Scope and Delimitations
This study focuses on the design and development of an AI-based monitoring system specifically for the TMC of Malaybalay City. The system processes video input from fixed cameras to detect and monitor multicab activity within yellow box zones. 

The scope includes system development, testing, and evaluation under field-simulated conditions using actual CCTV footage. A web-based dashboard is developed for authorized personnel. The delimitation of the study includes its primary focus on **Multicabs** as the monitored vehicle type. Other violations, such as speeding or counterflowing, are beyond the scope of this research.

---

## 2. REVIEW OF RELATED LITERATURE
### 2.1 Related Literature
Traffic monitoring is a critical component of urban management. Traditional monitoring in the Philippines relies heavily on manual observation, which restricts continuous response (DOTr, 2023). Ho et al. (2019) demonstrated that camera-based roadside occupation surveillance systems can effectively detect vehicles occupying restricted road spaces. Similarly, Rathore et al. (2021) showed that intelligent traffic monitoring integrating computer vision can provide real-time violation detection.

Artificial Intelligence, particularly YOLO models, allows traffic authorities to shift from reactive to proactive enforcement by providing data-driven monitoring (Basheer Ahmed et al., 2023). However, most existing systems focus on general traffic flow rather than the temporal analysis of "stop-time" duration within specific zones.

**Table 2-1. Comparison of Existing AI-Based Traffic Monitoring Systems**

| System / Study | Vehicle Detection | AI Processing | Camera Input | Real-Time | Stop-Time Tracking |
|----------------|:-----------------:|:-------------:|:------------:|:---------:|:------------------:|
| Traffic-Net (Rezaei et al., 2022) | ✓ | ✓ | ✓ | ✓ | ✗ |
| TRAMON (Tan & Kieu, 2023) | ✓ | ✓ | ✓ | ✓ | ✗ |
| Smart Traffic Control (Rathore, 2021) | ✓ | ✓ | ✓ | ✓ | ✗ |
| **Proposed System (Multicab-YBZ)** | **✓** | **✓** | **✓** | **✓** | **✓** |

### 2.2 Research Gap
Existing studies successfully implement AI-driven vehicle detection but primarily focus on counting, incident detection, or vehicle tracking. There is a clear gap in the automated measurement of stop-time duration within restricted yellow box zones, specifically for public transport vehicles like multicabs. This research addresses this gap by integrating a custom multi-object tracking algorithm that calculates the precise duration a vehicle remains stationary within a restricted zone.

### 2.3 Concept of the Study
The conceptual framework involves CCTV cameras capturing real-time video footage of regulated intersections. This footage is processed by a YOLOv8-based detection model to identify Multicabs. Once detected, a **Custom Kalman Centroid Tracker** tracks the vehicle's movement. If the vehicle's stop duration exceeds the allowable limit (e.g., 30 seconds inside the yellow box), a violation event is triggered, recorded in a SQLite database, and displayed on the TMC Dashboard.

### 2.4 Definition of Terms
- **Artificial Intelligence (AI)**: Simulation of human intelligence in machines to perform detection and analysis.
- **YOLO (You Only Look Once)**: A real-time object detection algorithm used for multicab identification.
- **Yellow Box Zone**: A marked intersection area where vehicles are prohibited from stopping.
- **Stop-Time Monitoring**: The process of measuring how long a vehicle remains stationary using tracking anchors.
- **Kalman Filter**: An algorithm used to predict and smooth vehicle tracking positions over consecutive frames.

---

## 3. METHODOLOGY
### 3.1 Materials
#### 3.1.1 Software
- **Python 3.10**: Primary language for AI logic and the Flask backend.
- **YOLOv8 (Ultralytics)**: Real-time detection and classification model.
- **Flask**: Backend framework managing API routes and system configuration.
- **React & Vite**: Frontend for the TMC Dashboard and evidence review.
- **SQLite**: Lightweight database for violation records, metadata, and logs.
- **OpenCV**: Library for video frame extraction and image preprocessing.

#### 3.1.2 Hardware
- **CCTV Camera**: 1080p, 30 fps high-definition camera.
- **Processing Station**: Intel i7 Processor, 16GB RAM, and NVIDIA GTX GPU for real-time model inference.

#### 3.1.3 Data Sources
- **TMC CCTV Footage**: Video recordings from Malaybalay City intersections (2025-2026).
- **Annotated Dataset**: Localized images of Multicabs annotated using LabelImg for model fine-tuning.

### 3.2 Methods
#### 3.2.1 Research Design
This study utilizes a **Developmental Research Design**, following the **Waterfall Model** (Plan, Develop, Implement, Evaluate, and Maintain) to ensure a structured engineering approach to the software lifecycle.

#### 3.2.2 System Implementation Procedures
1. **Requirements Gathering**: Consultations with TMC personnel to define stop-time thresholds (e.g., 20-30 seconds).
2. **AI Development**: Training YOLOv8 on localized Multicab datasets.
3. **Tracking Innovation**: Implementation of a **5-point anchor matching** mechanism (Top-Left, Top-Right, Center, Bottom-Left, Bottom-Right) to uniquely identify vehicles through occlusions.
4. **Backend Integration**: Developing a Flask API to handle real-time violation alerts and SQLite database interactions.
5. **Dashboard Development**: Creating a React-based interface for officers to view live feeds with AI overlays and historical violation logs.

#### 3.2.4 Violation Documentation (NCAP-Based)
The system adopts a **no-contact documentation approach**. When a violation is detected, the system records:
- High-resolution snapshot of the multicab.
- Timestamp and location.
- Total stop duration (e.g., "35.2 seconds").
- Detection confidence score.
This serves as a **decision-support tool** for TMC officers, who verify the evidence before enforcement action is taken.

#### 3.2.5 Handling Multiple Vehicles
To manage high-traffic intersections, the system employs the **5-point Kalman Tracker**. Each vehicle is assigned a unique ID. The tracking algorithm predicts the movement of multiple vehicles simultaneously, ensuring that overlapping Multicabs do not interfere with each other’s independent stop-time timers.

#### 3.2.6 Evaluation Metrics
The system is evaluated based on three categories using a 5-point Likert Scale:

| Category | Indicator | 5 (SA) | 4 (A) | 3 (N) | 2 (D) | 1 (SD) |
|----------|-----------|:---:|:---:|:---:|:---:|:---:|
| **Functionality** | Accurate detection and stop-time measurement. | | | | | |
| | Correct identification of multiple vehicles. | | | | | |
| **Usability** | The dashboard interface is intuitive and easy to navigate. | | | | | |
| | Real-time alerts are clear and timely. | | | | | |
| **Reliability** | Consistent performance under varying lighting and rain. | | | | | |
| | The system handles peak traffic without crashing. | | | | | |

*SA = Strongly Agree, A = Agree, N = Neutral, D = Disagree, SD = Strongly Disagree*
